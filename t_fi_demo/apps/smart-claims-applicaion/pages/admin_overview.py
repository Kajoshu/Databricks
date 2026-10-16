"""Admin Mode — Overview tab: KPIs, filters, and claims table."""
import streamlit as st
from components.kpi_cards import render_kpi_cards
from components.filters import render_filters
from db import query_df
from config import CLAIMS_SYNCED_TABLE


def render():
    col_t, col_b = st.columns([3, 1])
    with col_t:
        st.markdown("## \U0001f4cb All Claims Management")
        st.caption("Overview and management of all submitted claims")
    with col_b:
        if st.button("\U0001f4ca Analysis View", type="primary"):
            st.session_state.admin_tab = "analysis"
            st.rerun()

    render_kpi_cards()
    st.divider()

    filters = render_filters()
    st.divider()

    # ---- build WHERE clause ----
    clauses, params = [], []
    if filters["severity"] != "All Severity":
        clauses.append("severity = %s")
        params.append(filters["severity"])
    if filters["status"] == "Under Review":
        clauses.append("needs_review = true")
    elif filters["status"] == "Approved":
        clauses.append("needs_review = false")
    if filters["search"]:
        clauses.append(
            "(claim_no ILIKE %s OR policy_no ILIKE %s "
            "OR firstname ILIKE %s OR lastname ILIKE %s)"
        )
        like = f"%{filters['search']}%"
        params.extend([like, like, like, like])

    where = " AND ".join(clauses) if clauses else "1=1"

    df = query_df(
        f"""
        SELECT claim_no, policy_no, claim_date, total, severity,
               CASE WHEN needs_review THEN 'Under Review' ELSE 'Approved' END AS status,
               COALESCE(
                   (damage_prediction->>'score')::float * 100, 0
               )::int AS risk_score,
               firstname || ' ' || lastname AS customer_name
        FROM {CLAIMS_SYNCED_TABLE}
        WHERE {where}
        ORDER BY claim_date DESC
        LIMIT 100
        """,
        params or None,
    )

    st.markdown("### Claims List")
    st.caption("Click on any claim to view detailed analysis")

    if df.empty:
        st.info("No claims match your filters.")
        return

    st.dataframe(
        df,
        column_config={
            "claim_no":      st.column_config.TextColumn("Claim Number", width="medium"),
            "policy_no":     st.column_config.TextColumn("Policy", width="small"),
            "claim_date":    st.column_config.DateColumn("Date", width="small"),
            "total":         st.column_config.NumberColumn("Amount", format="$%d"),
            "severity":      st.column_config.TextColumn("Severity"),
            "status":        st.column_config.TextColumn("Status"),
            "risk_score":    st.column_config.ProgressColumn("Risk Score", min_value=0, max_value=100),
            "customer_name": st.column_config.TextColumn("Customer"),
        },
        hide_index=True,
        use_container_width=True,
        selection_mode="single-row",
        on_select="rerun",
        key="claims_table",
    )

    # Handle row selection -> jump to analysis
    sel = st.session_state.get("claims_table")
    if sel and sel.get("selection", {}).get("rows"):
        idx = sel["selection"]["rows"][0]
        st.session_state.selected_claim_no = df.iloc[idx]["claim_no"]
        st.session_state.admin_tab = "analysis"
        st.rerun()
