import streamlit as st
import pandas as pd
from database import fetch_all

def render_admin_dashboard():
    st.markdown('<div class="brand-header">🛡️ System Administration</div>', unsafe_allow_html=True)
    st.write("Welcome, System Administrator. Monitor and audit patient records centrally below.")
    
    # 1. System Statistics
    users_data = fetch_all('SELECT * FROM users WHERE is_admin = 0')
    predictions_data = fetch_all('SELECT * FROM predictions')
    
    total_users = len(users_data)
    total_assessments = len(predictions_data)
    high_risk_count = sum(1 for p in predictions_data if float(p[3]) > 65.0) # p[3] is risk_level
    
    st.markdown("### Platform Analytics")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Registered Patients", total_users)
    with c2:
        st.metric("Total Assessments Run", total_assessments)
    with c3:
        st.metric("Critical High-Risk Cases", high_risk_count)
        
    st.markdown("---")
    
    # 2. Users Table
    st.markdown("### Patient Directory")
    if users_data:
        df_users = pd.DataFrame(users_data, columns=["ID", "Name", "Age", "Gender", "Mobile", "Email", "PasswordHash", "IsAdmin"])
        df_users = df_users.drop(columns=["PasswordHash", "IsAdmin"])
        st.dataframe(df_users, use_container_width=True)
    else:
        st.info("No patients registered yet.")
        
    st.markdown("---")
    
    # 3. All Predictions History
    st.markdown("### Global Assessment Logs")
    if predictions_data:
        df_preds = pd.DataFrame(predictions_data, columns=["ID", "Patient Email", "Date Executed", "Calculated Risk (%)", "Assigned Tier", "Raw JSON Input"])
        df_preds = df_preds.drop(columns=["Raw JSON Input"])
        df_preds["Calculated Risk (%)"] = df_preds["Calculated Risk (%)"].apply(lambda x: f"{x:.1f}%")
        st.dataframe(df_preds.sort_values(by="Date Executed", ascending=False), use_container_width=True)
    else:
        st.info("No assessments have been run by any users yet.")

