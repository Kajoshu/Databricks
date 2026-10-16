# --- diagnostics bootstrap: install crash/exception logging before app code ---
import os as _diag_os
import sys as _diag_sys

_diag_dir = _diag_os.path.dirname(_diag_os.path.abspath(__file__))
if _diag_dir not in _diag_sys.path:
    _diag_sys.path.insert(0, _diag_dir)
import app_diagnostics  # noqa: E402

app_diagnostics.install_diagnostics()
# --- end diagnostics bootstrap ---

import streamlit as st

st.set_page_config(page_title="Smart Claims", page_icon="\U0001f535", layout="wide")

# Hide Streamlit's auto-discovered pages sidebar
st.markdown(
    """<style>[data-testid="stSidebar"] {display: none}</style>""",
    unsafe_allow_html=True,
)

# ---- initialise session state ----
if "mode" not in st.session_state:
    st.session_state.mode = "customer"
if "admin_tab" not in st.session_state:
    st.session_state.admin_tab = "overview"
if "customer_tab" not in st.session_state:
    st.session_state.customer_tab = "submit"

# ---- header (branding + mode toggle + tab nav) ----
from components.header import render_header  # noqa: E402

render_header()

# ---- route to the active page ----
if st.session_state.mode == "admin":
    if st.session_state.get("admin_tab") == "analysis":
        from pages.admin_analysis import render  # noqa: E402
    else:
        from pages.admin_overview import render  # noqa: E402
    render()
else:
    if st.session_state.get("show_results"):
        from pages.customer_results import render  # noqa: E402
    elif st.session_state.get("customer_tab") == "status":
        from pages.customer_status import render  # noqa: E402
    else:
        from pages.customer_submit import render  # noqa: E402
    render()
