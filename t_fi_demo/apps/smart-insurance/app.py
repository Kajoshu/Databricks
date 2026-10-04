import streamlit as st
import datetime
import uuid

def render_portal(policy):
    # Top header bar matching screenshot layout
    col_h1, col_h2 = st.columns([4, 1])
    with col_h1:
        st.markdown("### 🛡️ Smart Claims")
        st.caption("Claims Submission")
    with col_h2:
        if st.button("Sign Out", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.policy_data = None
            st.rerun()

    st.markdown("<hr style='margin: 0px 0px 20px 0px;'>", unsafe_allow_html=True)

    # Main Card Container
    st.markdown("<h2 style='text-align: center;'>Submit Your Claim</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Upload your accident image and provide claim details for instant analysis</p>", unsafe_allow_html=True)

    # File Uploader for Damage Images (Unity Catalog Volume target)
    uploaded_file = st.file_uploader("Upload a car damage image", type=["jpg", "jpeg", "png"])
    
    st.markdown("### Claim Details")
    st.caption("Please provide accurate information about your incident")

    with st.form("claim_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Policy number pre-filled and locked from auth
            policy_no_input = st.text_input("Policy Number *", value=policy.get("POLICY_NO"), disabled=True)
            sum_insured = float(policy.get("SUM_INSURED", 0.0))
            
            claim_amount = st.number_input(f"Claim Amount ($) [Max: ${sum_insured:,.2f}] *", min_value=0.0, step=100.0, value=1500.0)
            self_assessed_severity = st.selectbox("Self-Assessed Severity *", ["Minor", "Moderate", "Major"])
            vehicles_involved = st.number_input("Vehicles Involved *", min_value=1, max_value=10, value=1)

        with col2:
            accident_location = st.text_input("Accident Location *", placeholder="Enter location")
            accident_date = st.date_input("Accident Date *", datetime.date.today())
            collision_type = st.selectbox("Collision Type *", ["Rear-end", "Side-impact", "Head-on", "Single-vehicle"])
            number_of_witnesses = st.number_input("Number of Witnesses", min_value=0, max_value=10, value=0)

        submit_btn = st.form_submit_button("Submit Claim", use_container_width=True)

        if submit_btn:
            # Validation: Block claims exceeding maximum coverage limit
            if not accident_location:
                st.error("Please enter the accident location.")
            elif claim_amount > sum_insured:
                st.error(f"❌ **Claim Exceeds Coverage Limit:** The entered amount (${claim_amount:,.2f}) is greater than your maximum policy limit (${sum_insured:,.2f}). Please correct the amount.")
            else:
                with st.spinner("Processing claim through risk assessment..."):
                    claim_no = str(uuid.uuid4())
                    
                    # Optional: Handle image persistence to Unity Catalog Volume path here
                    file_path = "N/A"
                    if uploaded_file is not None:
                        # e.g., save to /Volumes/joshuandegwa_gold/default/damage_images/
                        file_path = f"/Volumes/joshuandegwa_gold/default/damage_images/{claim_no}_{uploaded_file.name}"

                    # ML Model Scoring Endpoint Integration
                    try:
                        import mlflow.deployments
                        client = mlflow.deployments.get_deploy_client("databricks")
                        response = client.predict(
                            endpoint="joshuandegwa-claim-risk-endpoint",
                            inputs=[{"claim_amount": claim_amount, "sum_insured": sum_insured}]
                        )
                        is_suspicious = bool(response[0].get("is_high_risk", False))
                    except Exception:
                        # Fallback threshold logic if endpoint is offline
                        is_suspicious = claim_amount > (sum_insured * 0.75)

                    # Build record mapped to your Gold target schema
                    claim_record = {
                        "claim_no": claim_no,
                        "policy_no": policy.get("POLICY_NO"),
                        "cust_id": policy.get("CUST_ID"),
                        "claim_date": str(datetime.date.today()),
                        "total": claim_amount,
                        "collision_type": collision_type,
                        "number_of_vehicles_involved": vehicles_involved,
                        "severity": self_assessed_severity,
                        "number_of_witnesses": number_of_witnesses,
                        "incident_date": str(accident_date),
                        "location": accident_location,
                        "image_path": file_path
                    }

                # Panic-Free Feedback Loop
                if is_suspicious:
                    st.info("ℹ️ **Status Update:** Your claim has been successfully received and routed for standard verification. Our team will review the details shortly.")
                else:
                    st.success("✅ **Claim Submitted Successfully!** Your claim is processed and queued for payout. Expect updates within 5 business days.")
                    st.balloons()