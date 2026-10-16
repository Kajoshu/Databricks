"""Customer Mode — Check Claim Status page."""
import streamlit as st
from db import query_df


def render():
    st.markdown("## Check Claim Status")
    st.caption("Enter your claim number to view the current status of your claim")

    claim_no = st.text_input(
        "Claim Number",
        placeholder="Enter your claim number",
        key="status_claim_no",
    )

    if not claim_no:
        st.info("Please enter your claim number above to look up your claim.")
        return

    # Look up the claim
    try:
        df = query_df(
            """
            SELECT claim_no, policy_no, claim_date, total, severity,
                   collision_type, firstname, lastname, borough, address,
                   CASE WHEN needs_review THEN 'Under Review' ELSE 'Approved' END AS status,
                   damage_prediction, image_name
            FROM smart_claims.claims_synced
            WHERE claim_no = %s
            LIMIT 1
            """,
            (claim_no.strip(),),
        )
    except Exception as e:
        st.error(f"Could not look up claim: {e}")
        return

    if df.empty:
        st.warning("No claim found with that number. Please check and try again.")
        return

    claim = df.iloc[0]

    # ---- Status banner ----
    status = claim["status"]
    if status == "Approved":
        st.success(
            f"\U0001f389 **Your claim has been approved.**\n\n"
            f"You will receive your refund within 3-5 business days.\n\n"
            f"**Claim Number:** {claim['claim_no']}  \n"
            f"**Status:** Approved"
        )
    else:
        st.warning(
            f"\u23f3 **Your claim is under review.**\n\n"
            f"Our team is currently reviewing your claim.\n\n"
            f"**Claim Number:** {claim['claim_no']}  \n"
            f"**Status:** Under Review"
        )

    # ---- Claim details ----
    st.markdown("### Claim Details")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Policy Number:** {claim.get('policy_no', 'N/A')}")
        st.markdown(f"**Claim Date:** {claim.get('claim_date', 'N/A')}")
        st.markdown(f"**Claim Amount:** ${claim.get('total', 0):,.2f}")
        st.markdown(f"**Severity:** {claim.get('severity', 'N/A')}")
    with col2:
        st.markdown(f"**Collision Type:** {claim.get('collision_type', 'N/A')}")
        st.markdown(f"**Customer:** {claim.get('firstname', '')} {claim.get('lastname', '')}")
        st.markdown(f"**Location:** {claim.get('borough', 'N/A')}")

    # ---- AI Damage Assessment ----
    prediction = claim.get("damage_prediction")
    if prediction:
        import json
        if isinstance(prediction, str):
            try:
                prediction = json.loads(prediction)
            except (json.JSONDecodeError, TypeError):
                prediction = None

        if prediction:
            label = prediction.get("label", "unknown")
            score = prediction.get("score", 0)
            colour = {"minor": "#FF9800", "major": "#F44336"}.get(label, "#9E9E9E")
            pct = f"{float(score) * 100:.0f}"
            st.markdown("### AI Damage Assessment")
            st.markdown(
                f"<div style='background:linear-gradient(135deg,{colour}22,{colour}11);"
                f"border-left:4px solid {colour};border-radius:12px;padding:20px;"
                f"margin:12px 0;max-width:400px'>"
                f"<p style='margin:0 0 6px;font-size:14px;color:#888'>Model Prediction</p>"
                f"<p style='margin:0;font-size:28px;font-weight:700;color:{colour}'>"
                f"{label.title()}</p>"
                f"<p style='margin:4px 0 0;font-size:14px;color:#666'>"
                f"Confidence: <strong>{pct}%</strong></p></div>",
                unsafe_allow_html=True,
            )
