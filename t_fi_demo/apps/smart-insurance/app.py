import streamlit as st
import datetime
import uuid

# Page setup
st.set_page_config(
    page_title="Smart Claims Portal",
    page_icon="🛡️",
    layout="centered"
)

# App Header
col_h1, col_h2 = st.columns([4, 1])
with col_h1:
    st.markdown("### 🛡️ Smart Claims")
    st.caption("Claims Submission & Automated Analysis")
with col_h2:
    st.markdown("👤 **Customer Mode**")

st.markdown("<hr style='margin: 0px 0px 20px 0px;'>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center;'>Submit Your Claim</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Upload your accident image and provide policy and claim details for instant analysis</p>", unsafe_allow_html=True)

# Image Uploader (Unity Catalog Volume target)
uploaded_file = st.file_uploader("Upload a car damage image", type=["jpg", "jpeg", "png"])

st.markdown("### Claim Details")
st.caption("Please provide accurate information about your incident")

with st.form("claim_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        # User explicitly enters policy number here
        input_policy = st.text_input("Policy Number *", placeholder="e.g., 102122649")
        claim_amount = st.number_input("Claim Amount ($) *", min_value=0.0, step=100.0, value=1500.0)
        self_assessed_severity = st.selectbox("Self-Assessed Severity *", ["Minor", "Moderate", "Major"])
        vehicles_involved = st.number_input("Vehicles Involved *", min_value=1, max_value=10, value=1)

    with col2:
        accident_location = st.text_input("Accident Location *", placeholder="Enter location (Street / City)")
        accident_date = st.date_input("Accident Date *", datetime.date.today())
        collision_type = st.selectbox("Collision Type *", ["Rear-end", "Side-impact", "Head-on", "Single-vehicle"])
        number_of_witnesses = st.number_input("Number of Witnesses", min_value=0, max_value=10, value=0)

    submit_btn = st.form_submit_button("Submit Claim & Run Analysis", use_container_width=True)

    if submit_btn:
        if not input_policy or not accident_location:
            st.error("Please provide both a policy number and an accident location.")
        else:
            cleaned_policy = input_policy.strip()
            
            with st.spinner("Validating policy and running risk assessment..."):
                try:
                    # 1. Live query against bronze table to fetch policy limits and metadata
                    query = f"""
                        SELECT POLICY_NO, CUST_ID, MAKE, MODEL, SUM_INSURED 
                        FROM joshuandegwa_bronze.policies 
                        WHERE POLICY_NO = '{cleaned_policy}' 
                        LIMIT 1
                    """
                    policy_df = spark.sql(query).toPandas()
                    
                    if policy_df.empty:
                        st.error(f"❌ Policy '{cleaned_policy}' not found in our records. Please check the number.")
                    else:
                        policy = policy_df.iloc[0].to_dict()
                        sum_insured = float(policy.get("SUM_INSURED", 0.0))
                        
                        # 2. Enforce coverage limit validation upfront
                        if claim_amount > sum_insured:
                            st.error(f"❌ **Claim Exceeds Coverage:** The entered amount (${claim_amount:,.2f}) is higher than your maximum policy limit (${sum_insured:,.2f}) for your {policy.get('MAKE')} {policy.get('MODEL')}.")
                        else:
                            claim_no = str(uuid.uuid4())
                            file_path = f"/Volumes/joshuandegwa_gold/default/damage_images/{claim_no}_{uploaded_file.name}" if uploaded_file else "N/A"

                            # 3. ML Model Scoring Endpoint Integration
                            is_suspicious = False
                            image_rules_passed = True
                            
                            try:
                                import mlflow.deployments
                                client = mlflow.deployments.get_deploy_client("databricks")
                                response = client.predict(
                                    endpoint="joshuandegwa-claim-risk-endpoint",
                                    inputs=[{
                                        "policy_no": cleaned_policy,
                                        "claim_amount": claim_amount, 
                                        "sum_insured": sum_insured,
                                        "image_path": file_path,
                                        "collision_type": collision_type,
                                        "severity": self_assessed_severity
                                    }]
                                />
                                is_suspicious = bool(response[0].get("is_high_risk", False))
                                image_rules_passed = bool(response[0].get("image_rules_passed", True))
                            except Exception:
                                # Fallback logic if endpoint is warming up
                                if claim_amount > (sum_insured * 0.75) or uploaded_file is None:
                                    is_suspicious = True

                            # 4. User Feedback Routing (Panic-free)
                            if is_suspicious or not image_rules_passed:
                                st.info(f"ℹ️ **Status Update:** Claim received for your {policy.get('MAKE')} {policy.get('MODEL')}. It has been routed for standard verification and our team will follow up shortly.")
                            else:
                                st.success(f"✅ **Claim Verified & Approved!** Your claim for policy `{cleaned_policy}` has passed automated checks. Expect payout processing within 5 business days.")
                                st.balloons()
                                
                except Exception as e:
                    st.error(f"❌ System error during verification: {str(e)}")