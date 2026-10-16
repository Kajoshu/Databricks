"""KPI metric card components for the admin overview."""
import streamlit as st
from db import query_df


@st.cache_data(ttl=60)
def _get_kpi_data():
    return query_df("""
        SELECT
            COUNT(*)                                                  AS total_claims,
            SUM(CASE WHEN severity = 'Total Loss'   THEN 1 ELSE 0 END) AS total_loss,
            SUM(CASE WHEN severity = 'Major Damage'  THEN 1 ELSE 0 END) AS major_damage,
            SUM(CASE WHEN severity = 'Minor Damage'  THEN 1 ELSE 0 END) AS minor_damage,
            COALESCE(SUM(total), 0)                                   AS total_amount
        FROM smart_claims.claims_synced
    """).iloc[0].to_dict()


def render_kpi_cards():
    """Render the five KPI metric cards."""
    kpis = _get_kpi_data()
    cols = st.columns(5)
    metrics = [
        ("\U0001f4cb", "Total Claims",  f"{int(kpis['total_claims']):,}"),
        ("\U0001f534", "Total Loss",    f"{int(kpis['total_loss']):,}"),
        ("\U0001f7e0", "Major Damage",  f"{int(kpis['major_damage']):,}"),
        ("\U0001f7e2", "Minor Damage",  f"{int(kpis['minor_damage']):,}"),
        ("\U0001f4b0", "Total Amount",  f"${kpis['total_amount']:,.0f}"),
    ]
    for i, (icon, label, value) in enumerate(metrics):
        with cols[i]:
            st.metric(label=f"{icon} {label}", value=value)
