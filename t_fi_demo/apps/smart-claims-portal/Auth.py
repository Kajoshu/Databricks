import os
import streamlit as st
import datetime
import pandas as pd
from databricks import sql as dbsql

# Page configuration
st.set_page_config(
    page_title="Smart Claims Portal - Login",
    page_icon="🛡️",
    layout="centered"
)

# Initialize session state for login tracking
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.policy_data = None

def authenticate_policy(policy_number: str):
    """
    Dynamically queries the customer_claim_policy table via the Databricks SQL connector.
    """
    try:
        cleaned_policy = policy_number.strip()
        
        query = """
            SELECT policy_no, cust_id, policytype, pol_issue_date, pol_eff_date,
                   pol_expiry_date, make, model, model_year, chassis_no,
                   use_of_vehicle, product, sum_insured, premium, deductable
            FROM dbr_dev.joshuandegwa_gold.customer_claim_policy
            WHERE policy_no = ?
            LIMIT 1
        """

        server_hostname = os.environ["DATABRICKS_HOST"].replace("https://", "").rstrip("/")
        with dbsql.connect(
            server_hostname=server_hostname,
            http_path=os.environ["DATABRICKS_WAREHOUSE_HTTP_PATH"],
            access_token=os.environ["DATABRICKS_TOKEN"]
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, [cleaned_policy])
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()

        if not rows:
            return None, "Policy number not found in our database. Please check and try again."

        policy_record = dict(zip(columns, rows[0]))

        # Validate Expiry Date
        expiry_raw = policy_record.get("pol_expiry_date")
        if expiry_raw:
            if isinstance(expiry_raw, str):
                expiry_date = datetime.datetime.fromisoformat(expiry_raw.replace("Z", "+00:00"))
            else:
                expiry_date = pd.to_datetime(expiry_raw).to_pydatetime()
                
            if expiry_date.date() < datetime.date.today():
                return None, f"This policy expired on {expiry_date.strftime('%Y-%m-%d')}."

        return policy_record, None

    except Exception as e:
        # Database or connection error
        return None, f"Database error: {str(e)}"


# --- MAIN CONTROLLER FLOW ---
if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>🛡️ Smart Claims Portal</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Enter your policy number to log in and access your portal</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            input_policy = st.text_input("Policy Number", placeholder="e.g., 101000955/RI")
            login_btn = st.form_submit_button("Access Portal", use_container_width=True)
            
            if login_btn:
                if not input_policy:
                    st.error("Please enter your policy number.")
                else:
                    policy_record, error_message = authenticate_policy(input_policy)
                    
                    if error_message:
                        st.error(f"❌ {error_message}")
                    else:
                        st.session_state.logged_in = True
                        st.session_state.policy_data = policy_record
                        st.rerun()
else:
    # Once authenticated, import and render the claim submission portal from app.py
    import app
    app.render_claim_portal()