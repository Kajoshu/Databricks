import streamlit as st
import datetime

def render_claim_portal():
    policy = st.session_state.policy_data
    
    # Top Header & Logout
    col_head1, col_head2 = st.columns([4, 1])
    with col_head1:
        st.markdown(f"### 🛡️ Smart Claims <span style='color: gray; font-size: 16px;'>| Customer #{policy['cust_id']}</span>", unsafe_allow_html=True)
    with col_head2:
        if st.button("🔒 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.policy_data = None
            st.rerun()

    st.markdown("---")

    # Policy Summary Card
    with st.container(border=True):
        st.markdown(f"#### 📋 Active Policy Summary: `{policy['policy_no']}`")
        p_col1, p_col2, p_col3 = st.columns(3)
        with p_col1:
            st.metric("Insured Vehicle", f"{policy['make']} {policy['model']}")
        with p_col2:
            st.metric("Sum Insured", f"${policy['sum_insured']:,.2f}")
        with p_col3:
            st.metric("Deductible", f"${policy['deductable']:,.2f}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Submit Your Incident Claim</h3>", unsafe_allow_html=True)
    
    with st.form("claim_submission_form"):
        uploaded_file = st.file_uploader("Upload Car Damage Image", type=["jpg", "jpeg", "png"])
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            claim_amount = st.number_input("Claim Amount ($) *", min_value=0.0, step=0.01)
            self_assessed_severity = st.selectbox("Self-Assessed Severity *", ["Minor", "Moderate", "Severe"])
            collision_type = st.selectbox("Collision Type *", ["Rear-end", "Side-impact", "Head-on", "Single-vehicle"])
        with col2:
            accident_location = st.text_input("Accident Location *", placeholder="Enter location")
            accident_date = st.date_input("Accident Date *", value=datetime.date.today())
            vehicles_involved = st.number_input("Vehicles Involved *", min_value=1, value=1, step=1)
        
        submit_button = st.form_submit_button("Submit Claim & Run Analysis", use_container_width=True)
        
        if submit_button:
            if not accident_location:
                st.error("Please enter the accident location.")
            else:
                st.success(f"Claim successfully filed under policy **{policy['policy_no']}**!")
                st.balloons()