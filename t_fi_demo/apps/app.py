import streamlit as st
import datetime

# Page configuration
st.set_page_config(
    page_title="Smart Claims - Claims Submission",
    page_icon="🛡️",
    layout="centered"
)

# App Header / Navigation
st.markdown("### 🛡️ Smart Claims <span style='color: gray; font-size: 16px;'>| Claims Submission</span>", unsafe_allow_html=True)
if st.button("📁 Submit Claim"):
    pass

st.markdown("---")

# Main Form Container
st.markdown("<h2 style='text-align: center;'>Submit Your Claim</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Upload your accident image and provide claim details for instant analysis</p>", unsafe_allow_html=True)

with st.form("claim_submission_form"):
    
    # Image Upload Section
    st.markdown("##### ⬆️ Upload a car damage image")
    uploaded_file = st.file_uploader(
        "Drag and drop file here", 
        type=["jpg", "jpeg", "png"],
        help="Limit 200MB per file · JPG, JPEG, PNG"
    )
    
    st.markdown("---")
    st.markdown("#### Claim Details")
    st.markdown("<p style='color: gray; font-size: 14px;'>Please provide accurate information about your incident</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        policy_number = st.text_input("Policy Number *", placeholder="Enter your policy number")
        claim_amount = st.number_input("Claim Amount ($) *", min_value=0.0, value=0.0, step=0.01)
        self_assessed_severity = st.selectbox("Self-Assessed Severity *", ["Minor", "Moderate", "Severe"])
        
    with col2:
        accident_location = st.text_input("Accident Location *", placeholder="Enter location")
        accident_date = st.date_input("Accident Date *", value=datetime.date.today())
        collision_type = st.selectbox("Collision Type *", ["Rear-end", "Side-impact", "Head-on", "Single-vehicle"])
        
    vehicles_involved = st.number_input("Vehicles Involved *", min_value=1, value=1, step=1)
    
    submit_button = st.form_submit_button("Submit and Run Analysis", use_container_width=True)
    
    if submit_button:
        if not policy_number or not accident_location:
            st.error("Please fill out all required fields marked with *.")
        else:
            st.success("Claim submitted successfully! Triggering ML pipeline analysis...")