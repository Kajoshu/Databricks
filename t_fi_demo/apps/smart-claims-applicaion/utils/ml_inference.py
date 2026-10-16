"""ML inference for car damage classification.

Calls the 'claims_damage_level' Model Serving endpoint which runs a
fine-tuned ResNet-50 registered at dbr_dev.joshuandegwa_gold.claims_damage_level.
The model expects a DataFrame with a 'content' column (raw image bytes)
and returns {label, score} per image.
"""
import base64
import io
import random

import pandas as pd
import streamlit as st

ENDPOINT_NAME = "claims_damage_level"


def _get_serving_client():
    """Return the WorkspaceClient for endpoint invocation."""
    from databricks.sdk import WorkspaceClient

    return WorkspaceClient()


def predict_damage(image_bytes: bytes) -> dict:
    """Classify car damage from an uploaded image via Model Serving.

    Returns
    -------
    dict with 'label' (str: ok | minor | major) and 'score' (float 0-1).
    """
    try:
        w = _get_serving_client()
        # The model wrapper expects a DataFrame with a 'content' column (raw bytes).
        # The serving endpoint accepts dataframe_records with base64-encoded bytes.
        b64_content = base64.b64encode(image_bytes).decode("utf-8")

        response = w.serving_endpoints.query(
            name=ENDPOINT_NAME,
            dataframe_records=[{"content": b64_content}],
        )

        # Response shape: {"predictions": [{"label": "major", "score": 0.52}]}
        predictions = response.predictions
        if predictions and len(predictions) > 0:
            pred = predictions[0]
            if isinstance(pred, dict):
                return {
                    "label": pred.get("label", "unknown"),
                    "score": float(pred.get("score", 0)),
                }
            # If predictions is a list of lists (some pyfunc models)
            return {"label": str(pred), "score": 0.5}

    except Exception as e:
        # Fallback: if endpoint is unavailable (cold start, not deployed yet),
        # return a simulated prediction so the app remains functional.
        st.warning(
            f"Model endpoint unavailable ({type(e).__name__}). "
            f"Using simulated prediction.",
            icon="\u26a0\ufe0f",
        )
        labels = ["minor", "major"]
        label = random.choices(labels, weights=[0.5, 0.5], k=1)[0]
        return {"label": label, "score": round(random.uniform(0.40, 0.95), 4)}

    return {"label": "unknown", "score": 0.0}


def label_to_severity(label: str) -> str:
    """Map ML prediction label to insurance severity string."""
    return {"minor": "Minor Damage", "major": "Total Loss"}.get(
        label, "Unknown"
    )
