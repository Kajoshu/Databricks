"""Customer Mode — Claim Analysis Results page (shown after submit)."""
import streamlit as st
from db import query_df, execute_write
from utils.rule_engine import evaluate_rules
from config import CLAIMS_SYNCED_TABLE, ACTIONS_TABLE


def render():
    claim = st.session_state.get("submitted_claim")
    if not claim:
        st.warning("No claim submitted yet. Please submit a claim first.")
        return

    st.markdown("## Claim Analysis Results")
    st.caption("Your claim has been analyzed using AI-powered image recognition")

    # Look up policy data from the synced table to enrich the claim
    try:
        policy_rows = query_df(
            "SELECT sum_insured, pol_eff_date, pol_expiry_date, telematics_speed "
            f"FROM {CLAIMS_SYNCED_TABLE} WHERE policy_no = %s LIMIT 1",
            (claim["policy_no"],),
        )
        if not policy_rows.empty:
            row = policy_rows.iloc[0]
            claim.setdefault("sum_insured", row.get("sum_insured", 0))
            claim.setdefault("pol_eff_date", str(row.get("pol_eff_date", "")))
            claim.setdefault("pol_expiry_date", str(row.get("pol_expiry_date", "")))
            claim.setdefault("telematics_speed", row.get("telematics_speed"))
        else:
            st.info("Policy not found in system — running evaluation with submitted data only.")
    except Exception as e:
        st.warning(f"Could not look up policy data: {e}")

    # Run rule engine
    evaluation = evaluate_rules(claim)
    checks = evaluation["checks"]

    # ---- approval / under-review banner ----
    if evaluation["recommendation"] == "approve":
        st.success(
            f"\U0001f389 **Congratulations! Your claim has been approved.**\n\n"
            f"You will receive your refund within 3-5 business days.\n\n"
            f"**Claim Number:** {claim['claim_no']}  \n"
            f"**Status:** Approved"
        )
    else:
        st.warning(
            f"\u23f3 **Your claim is under review.**\n\n"
            f"Our team will review your claim and get back to you.\n\n"
            f"**Claim Number:** {claim['claim_no']}  \n"
            f"**Status:** Under Review"
        )

    # ---- Policy Form Analysis Results (4 check icons) ----
    st.markdown("### Policy Form Analysis Results")
    display_order = [
        ("reported_severity_check", "Severity Check",  "\u2714\ufe0f"),
        ("valid_amount",            "Policy Amount",   "\U0001f6e1\ufe0f"),
        ("valid_date",              "Policy Date",     "\U0001f4ca"),
        ("speed_check",             "Speed Check",     "\U0001f4c4"),
    ]
    cols = st.columns(4)
    for i, (key, label, icon) in enumerate(display_order):
        check = checks[key]
        passed = check["passed"]
        color = "#4CAF50" if passed else "#F44336"
        symbol = "\u2714" if passed else "\u2718"
        result_text = check.get("result", "")
        detail_text = check.get("detail", "")
        with cols[i]:
            st.markdown(
                f"<div style='text-align:center;padding:20px;background:#1e1e1e;"
                f"border-radius:12px;border:1px solid #333'>"
                f"<div style='width:60px;height:60px;background:{color};"
                f"border-radius:50%;display:inline-flex;align-items:center;"
                f"justify-content:center;font-size:28px;color:white;"
                f"margin-bottom:10px'>{symbol}</div>"
                f"<p style='margin:0 0 4px;font-weight:600;font-size:15px;color:#e0e0e0'>{label}</p>"
                f"<p style='margin:0 0 2px;font-size:13px;font-weight:600;color:{color}'>{result_text}</p>"
                f"<p style='margin:0;font-size:11px;color:#999'>{detail_text}</p></div>",
                unsafe_allow_html=True,
            )

    # Record auto-evaluation
    try:
        execute_write(
            f"INSERT INTO {ACTIONS_TABLE} (claim_no, action_type, admin_email, comment) "
            "VALUES (%s, %s, %s, %s)",
            (
                claim["claim_no"],
                "approve" if evaluation["recommendation"] == "approve" else "note",
                "system",
                f"Auto-evaluated. Risk: {evaluation['risk_assessment']}. "
                f"Recommendation: {evaluation['recommendation']}",
            ),
        )
    except Exception:
        pass  # non-critical

    # ---- Claim Reference Box ----
    st.markdown("")
    st.markdown(
        f"<div style='background:#1a1a2e;border:1px solid #16213e;border-radius:12px;"
        f"padding:20px;margin:16px 0;text-align:center'>"
        f"<p style='margin:0 0 8px;font-size:13px;color:#888;text-transform:uppercase;"
        f"letter-spacing:1px'>Your Claim Reference</p>"
        f"<p style='margin:0 0 8px;font-size:20px;font-weight:700;color:#e0e0e0;"
        f"font-family:monospace'>{claim['claim_no']}</p>"
        f"<p style='margin:0;font-size:12px;color:#666'>"
        f"Save this number for follow-up with our team</p></div>",
        unsafe_allow_html=True,
    )

    # ---- Submit Another ----
    st.markdown("")
    if st.button("\U0001f4cb Submit Another Claim", type="primary", use_container_width=False):
        st.session_state.pop("submitted_claim", None)
        st.session_state.show_results = False
        st.rerun()
