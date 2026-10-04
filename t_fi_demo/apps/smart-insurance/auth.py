import streamlit as st

# Page setup
st.set_page_config(
    page_title="Smart Claims Portal",
    page_icon="🛡️",
    layout="centered"
)

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.policy_no = None

# --- VIEW 1: LOGIN / POLICY CHECK ---
if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>🛡️ Smart Claims Portal</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Enter your policy number to log a claim</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            input_policy = st.text_input("Policy Number", placeholder="e.g., 101000955/RI")
            login_btn = st.form_submit_button("Verify Policy", use_container_width=True)
            
            if login_btn:
                if not input_policy:
                    st.error("Please enter a policy number.")
                else:
                    cleaned_policy = input_policy.strip()
                    
                    try:
                        # Query joshuandegwa_bronze.policies table
                        query = f"""
                            SELECT policy_no 
                            FROM joshuandegwa_bronze.policies 
                            WHERE policy_no = '{cleaned_policy}' 
                            LIMIT 1
                        """
                        df = spark.sql(query).toPandas()
                        
                        if not df.empty:
                            st.session_state.logged_in = True
                            st.session_state.policy_no = cleaned_policy
                            st.rerun()
                        else:
                            st.error("❌ Policy not found. Please provide a proper policy number.")
                            
                    except Exception as e:
                        # Fallback for local testing if spark session isn't active
                        if cleaned_policy == "101000955/RI":
                            st.session_state.logged_in = True
                            st.session_state.policy_no = cleaned_policy
                            st.rerun()
                        else:
                            st.error(f"❌ Policy not found in database. (Error: {str(e)})")

# --- VIEW 2: WELCOME SCREEN ---
else:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.success(f"✅ Policy Verified: **{st.session_state.policy_no}**")
    st.markdown("### Welcome! You are authorized to log a claim.")
    
    if st.button("Log Out / Test Another Policy", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.policy_no = None
        st.rerun()