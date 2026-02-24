import streamlit as st
import google.generativeai as genai
import pandas as pd
import numpy as np
import os

# ==========================================
# 1. Page Configuration & Setup
# ==========================================
# This MUST be the first Streamlit command
st.set_page_config(page_title="AuraFit AI", page_icon="⚡", layout="wide")

# Safely fetch the key from the hidden Streamlit Secrets vault
API_KEY = st.secrets.get("GEMINI_API_KEY")

if not API_KEY:
    st.error("⚠️ Gemini API Key missing. Please set 'GEMINI_API_KEY' in your Streamlit Cloud Secrets.")
    st.stop()

genai.configure(api_key=API_KEY)

# Initialize Session States
if 'outdoor_mode' not in st.session_state:
    st.session_state.outdoor_mode = False
if 'ai_plan' not in st.session_state:
    st.session_state.ai_plan = None
if 'current_feature' not in st.session_state:
    st.session_state.current_feature = None

# ==========================================
# 2. AI Logic & Prompt Engineering
# ==========================================
FEATURES = {
    "Full-body workout plan": "Create a detailed full-body workout plan tailored for the specific sport and position.",
    "Safe recovery training schedule": "Design a safe, structured recovery training schedule that carefully adapts to the listed injuries and risk zones.",
    "Tactical coaching tips": "Provide actionable tactical coaching tips to improve position-specific skills and game intelligence.",
    "Week-long nutrition guide": "Create a comprehensive week-long nutrition guide adapting to the specific dietary needs, allergies, and calorie goals.",
    "Personalized warm-up and cooldown routine": "Design a personalized, dynamic warm-up and static cooldown routine specific to the sport.",
    "Mental focus and pre-match visualization routine": "Provide a mental focus and pre-match visualization routine to build confidence and game readiness.",
    "Hydration and electrolyte strategy plan": "Outline a precise hydration and electrolyte strategy plan for pre, during, and post-activity.",
    "Positional decision-making drills": "Suggest specific, situational decision-making drills tailored to the player's position.",
    "Mobility workouts tailored for post-injury recovery": "Design gentle, effective mobility workouts strictly tailored for post-injury recovery and joint health.",
    "Stamina-building routines for tournament preparation": "Provide progressive stamina-building cardiovascular and muscular endurance routines for tournament preparation."
}

def get_temperature(feature_name):
    safe_features = [
        "Full-body workout plan", "Safe recovery training schedule", 
        "Personalized warm-up and cooldown routine", "Mobility workouts tailored for post-injury recovery", 
        "Stamina-building routines for tournament preparation"
    ]
    return 0.3 if feature_name in safe_features else 0.8

# ==========================================
# 3. CSS Injection: The "Glass OS" Engine
# ==========================================
def inject_custom_css(is_outdoor_mode):
    if is_outdoor_mode:
        card_bg = "rgba(20, 20, 20, 0.95)"
        border = "2px solid #FFFFFF"
        blur = "blur(0px)"
        text_shadow = "none"
    else:
        card_bg = "rgba(255, 255, 255, 0.08)"
        border = "1px solid rgba(255, 255, 255, 0.2)"
        blur = "blur(16px)"
        text_shadow = "0 2px 10px rgba(0,0,0,0.5)"

    css = f"""
    <style>
        .stApp {{ background: radial-gradient(circle at top left, #1a2a6c, #111524, #111524); }}
        .glass-card {{
            background: {card_bg};
            backdrop-filter: {blur};
            -webkit-backdrop-filter: {blur};
            border: {border};
            border-radius: 24px;
            padding: 24px;
            margin-bottom: 20px;
            color: white;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            text-shadow: {text_shadow};
            transition: all 0.3s ease;
        }}
        .glass-title {{ font-size: 1.2rem; font-weight: 500; color: rgba(255, 255, 255, 0.7); text-transform: uppercase; letter-spacing: 2px; margin-bottom: 8px; }}
        .glass-metric {{ font-size: 3.5rem; font-weight: 800; line-height: 1; margin: 0; background: linear-gradient(135deg, #fff 0%, #aaa 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .glass-accent-cyan {{ color: #00E5FF; text-shadow: 0 0 10px rgba(0, 229, 255, 0.4); }}
        .glass-accent-green {{ color: #00FFAA; text-shadow: 0 0 10px rgba(0, 255, 170, 0.4); }}
        .glass-accent-magenta {{ color: #FF00AA; text-shadow: 0 0 10px rgba(255, 0, 170, 0.4); }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def glass_metric_card(title, value, unit, accent_class):
    st.markdown(f"""
    <div class="glass-card">
        <div class="glass-title">{title}</div>
        <div class="glass-metric {accent_class}">{value} <span style="font-size: 1.5rem; font-weight: normal;">{unit}</span></div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 4. User Interface
# ==========================================
# Top Header
col_logo, col_toggle = st.columns([3, 1])
with col_logo:
    st.markdown("<h1 style='color: white; letter-spacing: 4px;'>⚡ AURAFIT AI COACH</h1>", unsafe_allow_html=True)
with col_toggle:
    st.session_state.outdoor_mode = st.toggle("☀️ Outdoor Mode", value=st.session_state.outdoor_mode)

inject_custom_css(st.session_state.outdoor_mode)

# Sidebar: Player Profile Data
st.sidebar.markdown("<h2 style='color: white;'>📋 Athlete Profile</h2>", unsafe_allow_html=True)
with st.sidebar.form("player_profile_form"):
    sport = st.text_input("Sport", placeholder="e.g., Soccer, Tennis")
    position = st.text_input("Position", placeholder="e.g., Striker, Point Guard")
    injury_history = st.text_area("Injuries / Risk Zones", placeholder="e.g., Tight hamstrings")
    training_prefs = st.text_area("Training Preferences", placeholder="e.g., HIIT, bodyweight")
    nutrition_reqs = st.text_area("Nutrition", placeholder="e.g., Vegan, 2500 cal")
    goal = st.text_input("Primary Goal", placeholder="e.g., Increase stamina")
    
    st.markdown("---")
    selected_feature = st.selectbox("AI Coach Focus:", list(FEATURES.keys()))
    submit_button = st.form_submit_button("GENERATE AI PLAYBOOK 🚀")

# Form Submission Logic
if submit_button:
    if not sport or not position:
        st.sidebar.warning("⚠️ Sport and Position are required.")
    else:
        with st.spinner("AI Coach is analyzing your profile..."):
            try:
                user_context = f"""
                **Athlete Profile:**
                - Sport: {sport} | Position: {position}
                - Injury/Risk: {injury_history}
                - Preferences: {training_prefs}
                - Nutrition: {nutrition_reqs}
                - Goal: {goal}
                """
                
                final_prompt = f"{user_context}\n\n**Task:**\n{FEATURES[selected_feature]}"
                current_temp = get_temperature(selected_feature)
                
                model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    system_instruction="Speak in the encouraging, informative, and safety-conscious tone of a professional youth sports coach. Format your response cleanly using markdown."
                )
                
                response = model.generate_content(
                    final_prompt,
                    generation_config=genai.types.GenerationConfig(temperature=current_temp)
                )
                
                # Store in session state so it survives UI reruns
                st.session_state.ai_plan = response.text
                st.session_state.current_feature = selected_feature
                
            except Exception as e:
                st.sidebar.error(f"🚨 API Error: {str(e)}")

# Main Content Tabs
tab1, tab2, tab3 = st.tabs(["🏠 Vitals", "🤖 AI Playbook", "📈 Analytics"])

with tab1:
    col1, col2, col3 = st.columns(3)
    with col1: glass_metric_card("Heart Rate", "68", "bpm", "glass-accent-magenta")
    with col2: glass_metric_card("Active Energy", "840", "kcal", "glass-accent-green")
    with col3: glass_metric_card("Readiness", "92", "10%", "glass-accent-cyan")

with tab2:
    if st.session_state.ai_plan:
        st.markdown(f"<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='color: #00FFAA;'>{st.session_state.current_feature}</h3>", unsafe_allow_html=True)
        st.markdown(st.session_state.ai_plan)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='glass-card' style='text-align: center; color: rgba(255,255,255,0.5);'>", unsafe_allow_html=True)
        st.markdown("<h3>No active playbook.</h3><p>Fill out your Athlete Profile in the sidebar and hit Generate.</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<div class='glass-title'>Weekly Intensity Load</div>", unsafe_allow_html=True)
    chart_data = pd.DataFrame(
        np.random.randint(40, 100, size=(7, 2)),
        columns=['Cardio', 'Strength'],
        index=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    )
    st.bar_chart(chart_data, color=["#00FFAA", "#FF00AA"])
    st.markdown("</div>", unsafe_allow_html=True)
