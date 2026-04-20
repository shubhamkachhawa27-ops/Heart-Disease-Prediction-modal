import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from fpdf import FPDF
import random
import json

from auth import login_user_email, create_user, reset_password
from database import execute_query, fetch_all, fetch_one
from chatbot import HealthcareChatbot
from admin import render_admin_dashboard

# Configure the app
st.set_page_config(page_title="CardioCare+", page_icon="🫀", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for UI/UX Redesign
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0F172A, #020617); color: white; }
    h1, h2, h3, p, span { color: #f8fafc; }
    .stSidebar { background-color: #1e293b !important; }
    .brand-header { font-size: 48px; font-weight: 800; background: -webkit-linear-gradient(45deg, #EF4444, #fca5a5); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; letter-spacing: -1px; }
    .sub-brand { text-align: center; color: #94a3b8; font-size: 18px; margin-bottom: 40px; }
    .section-title { font-size: 24px; font-weight: 700; margin-top: 20px; margin-bottom: 20px; color: #e2e8f0; border-bottom: 1px solid #334155; padding-bottom: 10px; }
    .streamlit-expanderHeader { font-size: 18px !important; font-weight: bold; color: #e2e8f0 !important; }
    .badge-low { background: linear-gradient(135deg, #22C55E, #16a34a); padding: 10px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 20px; }
    .badge-medium { background: linear-gradient(135deg, #F59E0B, #d97706); padding: 10px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 20px; }
    .badge-high { background: linear-gradient(135deg, #EF4444, #dc2626); padding: 10px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 20px; }
    div[data-baseweb="input"] > div { background-color: #1e293b !important; color: white !important; border: 1px solid #334155; }
    .doc-card { background-color: #1e293b; border-left: 5px solid #EF4444; padding: 20px; margin-bottom: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    .doc-title { font-size: 20px; font-weight: bold; color: #f8fafc; }
    .doc-spec { color: #94a3b8; font-size: 14px; margin-bottom: 10px; }
    .stApp > header { visibility: hidden !important; }
    .stDeployButton { display: none !important; }
    footer { visibility: hidden !important; }
    #MainMenu { visibility: hidden !important; }
</style>
""", unsafe_allow_html=True)

# --- STATE MANAGERS ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.email = ""
    st.session_state.name = ""
    st.session_state.is_admin = False
    st.session_state.just_logged_in = False

# --- MODEL LOADING ---
@st.cache_resource
def load_resources():
    try:
        model = joblib.load('models/rf_model.pkl')
        scaler = joblib.load('models/scaler.pkl')
        return model, scaler
    except FileNotFoundError:
        return None, None

model, scaler = load_resources()

# --- HELPER FUNCTIONS ---
def get_insights(risk_prob, f):
    insights = {'diet': [], 'exercise': [], 'lifestyle': [], 'medical': []}
    if f['chol'] > 240:
        insights['diet'].append("Strictly limit saturated fats. Avoid fast food and processed meats.")
        insights['diet'].append("Incorporate foods naturally rich in Omega-3 like Salmon.")
    elif f['chol'] > 200:
        insights['diet'].append("Adopt a plant-centric, Mediterranean-style diet.")
    if f['trestbps'] > 130:
        insights['diet'].append("Cut down sodium intake to less than 1,500 mg a day (DASH Diet).")
    if not insights['diet']:
        insights['diet'].append("Maintain your current balanced diet and stay hydrated.")

    if f['exang'] == 1 or f['oldpeak'] > 1.5:
        insights['exercise'].append("⚠️ Avoid all severe cardio. Only do medically supervised, gentle walks.")
    elif f['trestbps'] > 140:
        insights['exercise'].append("Engage in brisk walking (30 mins daily). Avoid heavy weightlifting to prevent sudden BP spikes.")
    else:
        insights['exercise'].append("Perform 150 minutes of moderate aerobic workouts per week.")
        
    insights['lifestyle'].append("Aim for at least 7-8 hours of uninterrupted sleep.")
    insights['lifestyle'].append("Practice meditation or breathing exercises to lower baseline stress.")
    if risk_prob > 0.4:
        insights['lifestyle'].append("Absolutely avoid smoking and minimize alcohol consumption.")

    if risk_prob > 0.65:
        insights['medical'].append("🚨 **CRITICAL**: Immediate consultation with a cardiologist is recommended.")
    elif f['cp'] in [0, 1, 2]:
        insights['medical'].append("Chest pain detected. Bring this up to your physician ASAP.")
    else:
        insights['medical'].append("Routine annual checkups are sufficient based on your current metrics.")
        
    return insights

def download_pdf_report(user, risk_prob, risk_label, insights, raw_features):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 18)
    pdf.cell(0, 10, "CardioCare+ Comprehensive Evaluation", new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(5)
    
    pdf.set_font("helvetica", size=12)
    pdf.cell(0, 8, f"Patient Name: {user}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"Date Evaluated: {datetime.now().strftime('%B %d, %Y')}", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(5)
    pdf.set_font("helvetica", 'B', 14)
    pdf.cell(0, 10, f"OVERALL RISK CLASSIFICATION: {risk_label} ({risk_prob:.1f}%)", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(5)
    pdf.set_font("helvetica", 'B', 14)
    pdf.cell(0, 10, "Provided Clinical Telemetry:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", size=11)
    for k, v in raw_features.items():
        pdf.cell(0, 6, f"> {k}: {v}", new_x="LMARGIN", new_y="NEXT")
        
    pdf.ln(10)
    pdf.set_font("helvetica", 'B', 14)
    pdf.cell(0, 10, "Personalized Care Plan:", new_x="LMARGIN", new_y="NEXT")
    
    for category, lines in insights.items():
        pdf.set_font("helvetica", 'B', 12)
        pdf.cell(0, 8, category.upper() + ":", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", size=11)
        for line in lines:
            line_clean = line.replace('⚠️', '!!').replace('🚨', '!!').replace('**', '')
            pdf.multi_cell(0, 6, f"- {line_clean}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)
        
    return bytes(pdf.output())

# --- APP LAYOUT ---
if not st.session_state.logged_in:
    st.markdown('<div class="brand-header">🫀 CardioCare+</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-brand">Your AI-Powered Cardiovascular Support Platform</div>', unsafe_allow_html=True)
    
    auth_col1, auth_col2, auth_col3 = st.columns([1,2,1])
    with auth_col2:
        auth_tabs = st.tabs(["🔑 Password Login", "📝 Register Patient"])
        
        with auth_tabs[0]:
            st.markdown("### Patient Portal")
            with st.form("login_form"):
                l_email = st.text_input("Email Address", key="log_email")
                l_pass = st.text_input("Password", type="password", key="log_pass")
                log_submit = st.form_submit_button("Access Dashboard", type="primary", use_container_width=True)
                
            if log_submit:
                user_data = login_user_email(l_email, l_pass)
                if user_data:
                    st.session_state.logged_in = True
                    st.session_state.email = l_email
                    st.session_state.name = user_data["name"]
                    st.session_state.is_admin = user_data["is_admin"]
                    st.session_state.just_logged_in = True
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

            st.markdown("---")
            with st.expander("Forgot Password?"):
                with st.form("reset_form"):
                    f_email = st.text_input("Registered Email", key="f_email")
                    f_mob = st.text_input("Registered Mobile Number", key="f_mob")
                    f_pass = st.text_input("New Password", type="password", key="f_pass")
                    f_submit = st.form_submit_button("Reset Password", type="primary")
                    
                if f_submit:
                    if reset_password(f_email, f_mob, f_pass):
                        st.success("Password reset successfully! You can now login above.")
                    else:
                        st.error("No account matching those details was found.")
                        
        with auth_tabs[1]:
            st.markdown("### New Patient Registration")
            with st.form("register_form"):
                col_a, col_b = st.columns(2)
                with col_a:
                    r_name = st.text_input("Full Name", key="reg_name")
                    r_age = st.number_input("Age", 1, 120, 30, key="reg_age")
                    r_gen = st.selectbox("Gender", ["Male", "Female", "Other"], key="reg_gen")
                with col_b:
                    r_mob = st.text_input("Mobile Number", key="reg_mob")
                    r_email = st.text_input("Email Address", key="reg_email")
                    r_pass = st.text_input("Create Password", type="password", key="reg_pass")
                    
                reg_submit = st.form_submit_button("Create Profile", type="primary", use_container_width=True)
                
            if reg_submit:
                if not r_name or not r_email or not r_pass:
                    st.warning("Please fill all compulsory fields.")
                else:
                    res = create_user(r_name, r_age, r_gen, r_mob, r_email, r_pass)
                    if res:
                        st.success("Successfully registered! You may now login via Password.")
                    else:
                        st.error("Email or Mobile already exists.")

else:
    if st.session_state.get("just_logged_in", False):
        st.toast(f"Login Successful! Welcome, {st.session_state.name}.", icon="🎉")
        st.session_state.just_logged_in = False

    # Navigation
    st.sidebar.markdown('<div class="brand-header" style="font-size:28px;">🫀 CardioCare+</div>', unsafe_allow_html=True)
    role_flag = "🛡️ Administrator" if st.session_state.is_admin else "👤 Patient"
    st.sidebar.markdown(f"> Welcome, **{st.session_state.name}**\n> *{role_flag}*")
    
    menu = ["🏠 Main Dashboard", "🔍 Smart Analytics", "💬 AI Cardiologist", "📅 Plan & Reminders", "🏥 Find Doctors"]
    if st.session_state.is_admin:
        menu.insert(0, "🛡️ Admin Console")
        
    choice = st.sidebar.radio("Care Modules", menu)
    
    if st.sidebar.button("🚪 Secure Logout"):
        st.session_state.clear()
        st.rerun()
        
    st.sidebar.caption("Data securely isolated utilizing AES Standard logic.")

    if choice == "🛡️ Admin Console":
        render_admin_dashboard()
        
    elif choice == "🏠 Main Dashboard":
        st.markdown('<div class="section-title">Telemetry & Engine Input</div>', unsafe_allow_html=True)
        
        if model is None:
            st.error("System Initialization failed: Model binaries missing.")
        else:
            with st.form("engine_params", border=True):
                st.write("Adjust the sliders below to reflect your most recent clinical outputs:")
                
                c1, c2 = st.columns(2)
                with c1:
                    age = st.slider("Patient Age", 1, 120, 50, help="Biological age heavily drives aggregate risk factors.")
                    trestbps = st.slider("Resting Blood Pressure (mmHg)", 80, 200, 120, help="Ideal is < 120. Values > 140 indicate hypertension.")
                    chol = st.slider("Serum Cholesterol (mg/dl)", 100, 600, 200, help="Above 200 is borderline; above 240 is considered dangerous.")
                    thalach = st.slider("Max Heart Rate Achieved (bpm)", 60, 220, 150, help="Maximum physiological capacity during stress.")
                    
                    sex = st.selectbox("Sex", options=[("Male", 1), ("Female", 0)], format_func=lambda x: x[0])
                    cp = st.selectbox("Chest Pain Experience", options=[
                        ("Typical Angina", 0), ("Atypical Angina", 1), 
                        ("Non-anginal Pain", 2), ("Asymptomatic", 3)
                    ], format_func=lambda x: x[0], help="Typical angina signifies oxygen depletion during stress.")
                    
                with c2:
                    oldpeak = st.slider("ST Depression (oldpeak)", 0.0, 6.0, 1.0, 0.1, help="ECG derivation evaluating blood flow latency.")
                    ca = st.slider("Major Vessels (0-4)", 0, 4, 0, help="Narrow/blocked vessels visualized via angiography.")
                    
                    fbs = st.selectbox("Fasting Blood Sugar > 120 mg/dl ?", options=[("Yes", 1), ("No", 0)], format_func=lambda x: x[0])
                    restecg = st.selectbox("Resting ECG Result", options=[
                        ("Normal", 0), ("ST-T wave abnormality", 1), ("Hypertrophy", 2)
                    ], format_func=lambda x: x[0])
                    exang = st.selectbox("Exercise Induced Angina", options=[("Yes", 1), ("No", 0)], format_func=lambda x: x[0])
                    slope = st.selectbox("Slope of Peak Exercise ST", options=[
                        ("Upsloping", 0), ("Flat", 1), ("Downsloping", 2)
                    ], format_func=lambda x: x[0])
                    thal = st.selectbox("Thalassemia (Hemoglobin Disturbance)", options=[
                        ("Normal", 1), ("Fixed Defect", 2), ("Reversable Defect", 3), ("Unknown", 0)
                    ], format_func=lambda x: x[0])

                submit_prediction = st.form_submit_button("Launch Diagnostic Scan", type="primary")

            if submit_prediction:
                input_df = pd.DataFrame([[
                    age, sex[1], cp[1], trestbps, chol, fbs[1], restecg[1], 
                    thalach, exang[1], oldpeak, slope[1], ca, thal[1]
                ]], columns=['age', 'sex', 'cp', 'trestbps', 'chol', 'fbs', 'restecg', 
                             'thalach', 'exang', 'oldpeak', 'slope', 'ca', 'thal'])
                             
                continuous_features = ['age', 'trestbps', 'chol', 'thalach', 'oldpeak']
                input_df[continuous_features] = scaler.transform(input_df[continuous_features])
                
                probability = model.predict_proba(input_df)[0][1] * 100
                
                bar_color = ""
                alert_class = ""
                if probability < 35:
                    label = "Low Risk"
                    bar_color = "#22C55E"
                    alert_class = "badge-low"
                    txt = "Excellent Outlook: Your metrics align with a healthy cardiovascular profile."
                elif probability < 65:
                    label = "Medium Risk"
                    bar_color = "#F59E0B"
                    alert_class = "badge-medium"
                    txt = "Moderate Outlook: Pay attention to rising parameters mapping closely to risk thresholds."
                else:
                    label = "High Risk"
                    bar_color = "#EF4444"
                    alert_class = "badge-high"
                    txt = "Critical Outlook: Action required to manage systemic heart failure variables."

                raw = {'age': age, 'trestbps': trestbps, 'chol': chol, 'fbs': fbs[1], 'cp': cp[1], 'exang': exang[1], 'oldpeak': oldpeak}
                
                st.markdown("---")
                g1, g2 = st.columns([1, 1.3])
                
                with g1:
                    st.markdown(f'<div class="{alert_class}">Heart Status: {label}</div>', unsafe_allow_html=True)
                    fig = go.Figure(go.Indicator(
                        mode = "gauge+number",
                        value = probability,
                        number = {'suffix': "%", 'font': {'color': 'white', 'size': 50}},
                        gauge = {
                            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "white"},
                            'bar': {'color': bar_color},
                            'bgcolor': 'rgba(0,0,0,0)',
                            'borderwidth': 0,
                            'steps': [
                                {'range': [0, 35], 'color': "rgba(34, 197, 94, 0.2)"},
                                {'range': [35, 65], 'color': "rgba(245, 158, 11, 0.2)"},
                                {'range': [65, 100], 'color': "rgba(239, 68, 68, 0.2)"}
                            ]
                        }
                    ))
                    fig.update_layout(height=350, margin=dict(l=10, r=10, b=10, t=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig, use_container_width=True)
                    st.caption(txt)

                with g2:
                    st.markdown('<div style="font-size: 20px; font-weight:bold; margin-bottom:10px;">📋 Patient-Specific Strategies</div>', unsafe_allow_html=True)
                    insights = get_insights(probability / 100.0, raw)
                    
                    with st.expander("🥗 Nutritional & Diet Plan", expanded=True):
                        for item in insights['diet']: st.write(f"• {item}")
                    with st.expander("🏃‍♂️ Physical Exercise Regimen", expanded=False):
                        for item in insights['exercise']: st.write(f"• {item}")
                    with st.expander("🧘 Lifestyle Adaptations", expanded=False):
                        for item in insights['lifestyle']: st.write(f"• {item}")
                    with st.expander("💊 Medical Diagnosis Action", expanded=False):
                        for item in insights['medical']: st.write(f"• {item}")

                date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # Store prediction dynamically inside `predictions` table
                execute_query('INSERT INTO predictions (user_email, date, risk_level, result, input_data) VALUES (?, ?, ?, ?, ?)',
                              (st.session_state.email, date_str, probability, label, json.dumps(raw)))
                              
                pdf_bytes = download_pdf_report(st.session_state.name, probability, label, insights, raw)
                st.download_button("📥 Save Medical Report (PDF)", data=pdf_bytes, file_name=f"Cardiac_Report_{st.session_state.name}.pdf", mime="application/pdf", type="primary")

    elif choice == "🔍 Smart Analytics":
        st.markdown('<div class="section-title">Macro Medical Profile & Trajectory</div>', unsafe_allow_html=True)
        history_data = fetch_all('SELECT date, risk_level, result, input_data FROM predictions WHERE user_email = ?', (st.session_state.email,))
        
        if len(history_data) == 0:
            st.info("Run an assessment first to unlock trajectory graphics.")
        else:
            df_hist = pd.DataFrame(history_data, columns=["Date", "Risk Level", "Result", "Input JSON"])
            df_hist['Date'] = pd.to_datetime(df_hist['Date'])
            
            t1, t2 = st.tabs(["📉 Trajectory Maps", "⚖️ Healthy Range Comparison"])
            
            with t1:
                fig = px.area(df_hist, x='Date', y='Risk Level', markers=True, color_discrete_sequence=['#EF4444'])
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", title="Calculated Risk (%) Over Time")
                st.plotly_chart(fig, use_container_width=True)
                
            with t2:
                latest_raw = json.loads(df_hist.iloc[-1]['Input JSON'])
                categories = ['Cholesterol', 'Resting BP', 'Max Heart Rate']
                patient_vals = [
                    latest_raw['chol'] / 300.0, 
                    latest_raw['trestbps'] / 200.0,
                    1.0  # Normalized fallback
                ]
                healthy_vals = [200/300.0, 120/200.0, 0.8]
                
                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(r=healthy_vals, theta=categories, fill='toself', name='Healthy Average', line_color='#22C55E'))
                fig.add_trace(go.Scatterpolar(r=patient_vals, theta=categories, fill='toself', name='Your Last Session Vitals', line_color='#EF4444'))
                fig.update_layout(polar=dict(radialaxis=dict(visible=False, range=[0, 1]), bgcolor="rgba(0,0,0,0)"), paper_bgcolor='rgba(0,0,0,0)', font_color="white")
                st.plotly_chart(fig, use_container_width=True)

    elif choice == "💬 AI Cardiologist":
        from ui_chat import render_chat_interface
        render_chat_interface(st.session_state.email)

    elif choice == "📅 Plan & Reminders":
        st.markdown('<div class="section-title">Pill & Appointment Scheduler</div>', unsafe_allow_html=True)
        c_left, c_right = st.columns([1,1.5])
        with c_left:
            with st.form("agenda_planner", border=True):
                st.write("#### Create Schedule")
                task = st.text_input("Intervention (e.g., 'Take Aspirin')")
                date = st.date_input("Target Runtime")
                if st.form_submit_button("Log Event", type="primary"):
                    execute_query('INSERT INTO reminders (user_email, task, date) VALUES (?, ?, ?)', (st.session_state.email, task, date))
                    st.success("Successfully synchronized to master schedule.")
        
        with c_right:
            rem_data = fetch_all('SELECT task, date FROM reminders WHERE user_email = ? ORDER BY date ASC', (st.session_state.email,))
            if len(rem_data) == 0:
                st.info("System has no recorded interventions.")
            else:
                for task, date in rem_data:
                    st.markdown(f'<div class="doc-card" style="border-left-color: #F59E0B; padding: 10px;"><b>{date}</b>: {task}</div>', unsafe_allow_html=True)

    elif choice == "🏥 Find Doctors":
        st.markdown('<div class="section-title">Specialist Locational Integration</div>', unsafe_allow_html=True)
        st.write("To locate a licensed Cardiology department, supply your physical routing code:")
        pin = st.text_input("Enter 5-digit ZIP / PIN Code:", placeholder="e.g. 90210")
        
        if st.button("Initialize Regional Scan", type="primary"):
            if len(pin) >= 4:
                map_url = f"https://www.google.com/maps?q=Cardiologists+and+Hospitals+near+{pin}"
                st.markdown(f"""
                <div class="doc-card">
                    <div class="doc-title">General Maps Inquiry Activated</div>
                    <div class="doc-spec">Radius bounded near '{pin}'</div>
                    <a href="{map_url}" target="_blank">
                        <button style="background-color: #EF4444; color: white; padding: 10px 15px; border-radius: 8px; border: none; cursor: pointer; margin-top:10px;">
                        🗺️ Get Directions & Call Features natively via Google Maps
                        </button>
                    </a>
                </div>
                """, unsafe_allow_html=True)
                
                st.write("##### Sample Nearest Registered Clinics (MOCK DATA)")
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("""<div class="doc-card" style="border-left-color:#22C55E;"><div class="doc-title">Dr. Sarah Jenkins</div><div class="doc-spec">Interventional Cardiologist (1.2 miles)</div><div>📞 (555) 123-4567</div></div>""", unsafe_allow_html=True)
                with c2:
                    st.markdown("""<div class="doc-card" style="border-left-color:#F59E0B;"><div class="doc-title">Heart Health Pavilion</div><div class="doc-spec">Cardiovascular Center (3.4 miles)</div><div>📞 (555) 987-6543</div></div>""", unsafe_allow_html=True)
            else:
                st.error("Invalid ZIP parameter supplied.")
