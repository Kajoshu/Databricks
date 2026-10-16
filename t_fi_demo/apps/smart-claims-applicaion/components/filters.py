"""Filter and search components for admin overview."""
import streamlit as st


def render_filters():
    """Render search bar, status dropdown, and severity dropdown.

    Returns a dict with keys: search, status, severity.
    """
    st.markdown("### \U0001f50d Filters & Search")
    c1, c2, c3 = st.columns([3, 2, 2])
    with c1:
        search = st.text_input(
            "Search", placeholder="Search claims...", label_visibility="collapsed"
        )
    with c2:
        status = st.selectbox(
            "Status",
            ["All Status", "Under Review", "Approved"],
            label_visibility="collapsed",
        )
    with c3:
        severity = st.selectbox(
            "Severity",
            ["All Severity", "Minor Damage", "Major Damage", "Total Loss"],
            label_visibility="collapsed",
        )
    return {"search": search, "status": status, "severity": severity}
