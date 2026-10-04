import streamlit as st
import pandas as pd
from databricks.connect import DatabricksSession

spark = DatabricksSession.builder.getOrCreate()

# Page setup
st.set_page_config(
    page_title="Smart Claims Portal - Login",
    page_icon="🛡️",
    layout="centered"
)

# Initialize session state for auth
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.policy_data = None

if not st.session_state.authenticated:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>🛡️ Smart Claims Portal</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Enter your policy number to access claim submission</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("auth_form"):
            input_policy = st.text_input("Policy Number", placeholder="e.g., 102122649")
            login_btn = st.form_submit_button("Access Portal", use_container_width=True)
            
            if login_btn:
                if not input_policy:
                    st.error("Please enter a policy number.")
                else:
                    cleaned_policy = input_policy.strip()
                    try:
                        # Query exact schema from your bronze table
                        query = f"""
                            SELECT POLICY_NO, CUST_ID, POLICYTYPE, POL_ISSUE_DATE, POL_EFF_DATE, 
                                   POL_EXPIRY_DATE, MAKE, MODEL, MODEL_YEAR, CHASSIS_NO, 
                                   USE_OF_VEHICLE, PRODUCT, SUM_INSURED, PREMIUM, DEDUCTABLE
                            FROM joshuandegwa_bronze.policies 
                            WHERE POLICY_NO = '{cleaned_policy}' 
                            LIMIT 1
                        """
                        df = spark.sql(query).toPandas()
                        
                        if not df.empty:
                            st.session_state.authenticated = True
                            st.session_state.policy_data = df.iloc[0].to_dict()
                            st.rerun()
                        else:
                            st.error("❌ Policy not found. Please provide a proper policy number.")
                    except Exception as e:
                        # Fallback mock data matching your schema for local dev testing
                        if cleaned_policy == "102122649":
                            st.session_state.authenticated = True
                            st.session_state.policy_data = {
                                "POLICY_NO": cleaned_policy,
                                "CUST_ID": 9990.0,
                                "POLICYTYPE": "COMP",
                                "MAKE": "RENAULT",
                                "MODEL": "MEGANE",
                                "MODEL_YEAR": 2015.0,
                                "SUM_INSURED": 32000.0,
                                "DEDUCTABLE": 1000
                            }
                            st.rerun()
                        else:
                            st.error(f"❌ Verification error or policy missing. ({str(e)})")
else:
    # Once authenticated, import and run the main portal UI
    import app
    app.render_portal(st.session_state.policy_data)