"""Admin Mode — Analysis tab: Claims Investigation view."""
import streamlit as st
import json
from db import query_df, execute_write
from utils.rule_engine import evaluate_rules


def render():
    st.markdown("## \U0001f4ca Claims Investigation Analysis")
    st.caption("Review and analyze submitted insurance claims")

    # severity filter
    _, col_sev = st.columns([4, 1])
    with col_sev:
        sev_filter = st.selectbox(
            "Severity",
            ["All Severity", "Minor Damage", "Major Damage", "Total Loss"],
            key="analysis_sev",
        )

    # ---- Search for a claim ----
    st.markdown("### \U0001f50d Find a Claim")
    search_col, btn_col = st.columns([5, 1])
    with search_col:
        search_term = st.text_input(
            "Search",
            placeholder="Enter policy number, claim number, or customer name\u2026",
            key="claim_search",
            label_visibility="collapsed",
        )
    with btn_col:
        search_clicked = st.button("Search", type="primary", use_container_width=True)

    # Build the claims list — either from search or default browse
    sev_where = f"AND severity = '{sev_filter}'" if sev_filter != "All Severity" else ""

    if search_term:
        like = f"%{search_term}%"
        claims_list = query_df(
            f"SELECT claim_no, policy_no, firstname || ' ' || lastname AS customer_name "
            f"FROM smart_claims.claims_synced "
            f"WHERE (claim_no ILIKE %s OR policy_no ILIKE %s "
            f"  OR firstname ILIKE %s OR lastname ILIKE %s) {sev_where} "
            f"ORDER BY claim_date DESC LIMIT 50",
            (like, like, like, like),
        )
        if claims_list.empty:
            st.warning("No claims found. Try a different search term.")
            return
    else:
        claims_list = query_df(
            f"SELECT claim_no, policy_no, firstname || ' ' || lastname AS customer_name "
            f"FROM smart_claims.claims_synced "
            f"WHERE 1=1 {sev_where} "
            f"ORDER BY claim_date DESC LIMIT 50"
        )
        if claims_list.empty:
            st.info("No claims available.")
            return

    # ---- Claim Navigation ----
    st.markdown("### \U0001f9ed Claim Navigation")
    options = claims_list["claim_no"].tolist()
    selected = st.session_state.get("selected_claim_no")
    cur_idx = options.index(selected) if selected and selected in options else 0

    nav1, nav2, nav3 = st.columns([3, 3, 1])
    with nav1:
        st.markdown(
            f"**{claims_list.iloc[cur_idx]['customer_name']}**"
        )
    with nav2:
        st.markdown(
            f"Policy: `{claims_list.iloc[cur_idx]['policy_no']}` \u00b7 "
            f"Claim: `{options[cur_idx][:16]}\u2026`"
        )
    with nav3:
        if st.button("Next Claim \u2192"):
            st.session_state.selected_claim_no = options[(cur_idx + 1) % len(options)]
            st.rerun()

    # ---- Load full claim ----
    claim_no = options[cur_idx]
    claim_df = query_df(
        "SELECT * FROM smart_claims.claims_synced WHERE claim_no = %s", (claim_no,)
    )
    if claim_df.empty:
        st.error("Claim not found.")
        return

    claim = claim_df.iloc[0].to_dict()
    dp = claim.get("damage_prediction", {})
    if isinstance(dp, str):
        try:
            dp = json.loads(dp)
        except (json.JSONDecodeError, TypeError):
            dp = {}
    claim["damage_prediction"] = dp

    evaluation = evaluate_rules(claim)
    checks = evaluation["checks"]

    st.divider()

    # ---- Rule Engine Test Results ----
    st.markdown("### \u2699\ufe0f Rule Engine Test Results")
    rule_items = [
        ("reported_severity_check", "Severity Check"),
        ("valid_amount",            "Policy Amount"),
        ("valid_date",              "Policy Date"),
        ("speed_check",             "Speed Check"),
    ]
    rc = st.columns(4)
    for i, (key, title) in enumerate(rule_items):
        ck = checks[key]
        color = "#4CAF50" if ck["passed"] else "#F44336"
        icon = "\u2714" if ck["passed"] else "\u2718"
        with rc[i]:
            st.markdown(
                f"<div style='text-align:center;padding:16px;background:#f8f9fa;"
                f"border-radius:12px;border-left:4px solid {color}'>"
                f"<p style='margin:0;color:#666;font-size:14px'>{title}</p>"
                f"<p style='margin:4px 0;color:{color};font-size:20px;"
                f"font-weight:bold'>{icon} {ck['result']}</p>"
                f"<p style='margin:0;color:#999;font-size:12px'>{ck['detail']}</p>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # Risk & Recommendation
    risk = evaluation["risk_assessment"]
    rec = evaluation["recommendation"]
    rcolors = {"low": "#4CAF50", "medium": "#FF9800", "high": "#F44336"}
    r1, r2 = st.columns(2)
    with r1:
        st.markdown(
            f"**Risk Assessment:** "
            f"<span style='color:{rcolors[risk]};font-size:20px;font-weight:bold'>"
            f"{risk.upper()}</span>",
            unsafe_allow_html=True,
        )
    with r2:
        st.markdown(
            f"**Recommendation:** "
            f"<span style='color:{rcolors.get(rec, '#666')};font-size:20px;"
            f"font-weight:bold'>{rec.capitalize()}</span>",
            unsafe_allow_html=True,
        )

    st.divider()

    # ---- Three detail panels ----
    d1, d2, d3 = st.columns(3)

    with d1:
        st.markdown("### \U0001f6e1\ufe0f Claim Details")
        st.markdown(
            f"| Field | Value |\n| --- | --- |\n"
            f"| Incident Type | {claim.get('type', 'N/A')} |\n"
            f"| Incident Severity | {claim.get('severity', 'N/A')} |\n"
            f"| Collision Type | {claim.get('collision_type', 'N/A')} |\n"
            f"| Vehicles Involved | {claim.get('number_of_vehicles_involved', 'N/A')} |\n"
        )

    with d2:
        st.markdown("### \U0001f4f7 Accident Image")
        img_name = claim.get("image_name", "")
        if img_name:
            try:
                from databricks.sdk import WorkspaceClient
                w = WorkspaceClient()
                vol_path = f"/Volumes/dbr_dev/joshuandegwa_bronze/images/claims/images/{img_name}"
                resp = w.files.download(vol_path)
                img_bytes = resp.contents.read()
                st.image(img_bytes, caption=img_name, use_column_width=True)
            except Exception as e:
                st.warning(f"Could not load image: {e}")
                st.info(f"Image file: {img_name}")
        else:
            st.info("No image available for this claim")

    with d3:
        st.markdown("### \U0001f464 Customer Information")
        st.markdown(
            f"| Field | Value |\n| --- | --- |\n"
            f"| Customer Name | {claim.get('firstname', '')} {claim.get('lastname', '')} |\n"
            f"| Policy Number | {claim.get('policy_no', 'N/A')} |\n"
            f"| Address | {claim.get('address', 'N/A')} |\n"
            f"| Location | {claim.get('borough', 'N/A')} |\n"
        )

    st.divider()

    # ---- Admin Actions ----
    st.markdown("### \U0001f4dd Admin Actions")
    a1, a2, a3 = st.columns([2, 2, 4])
    with a1:
        if st.button("\u2705 Approve", type="primary", use_container_width=True):
            execute_write(
                "INSERT INTO public.claim_actions "
                "(claim_no, action_type, admin_email, comment) VALUES (%s,%s,%s,%s)",
                (claim_no, "approve", "admin@smartclaims.com", "Approved after review"),
            )
            st.success("Claim approved!")
    with a2:
        if st.button("\u274c Deny", type="secondary", use_container_width=True):
            execute_write(
                "INSERT INTO public.claim_actions "
                "(claim_no, action_type, admin_email, comment) VALUES (%s,%s,%s,%s)",
                (claim_no, "deny", "admin@smartclaims.com", "Denied after review"),
            )
            st.error("Claim denied.")
    with a3:
        note = st.text_input("Add a note", placeholder="Enter note\u2026", key="admin_note")
        if note and st.button("\U0001f4ac Add Note"):
            execute_write(
                "INSERT INTO public.claim_actions "
                "(claim_no, action_type, admin_email, comment) VALUES (%s,%s,%s,%s)",
                (claim_no, "note", "admin@smartclaims.com", note),
            )
            st.success("Note added!")
