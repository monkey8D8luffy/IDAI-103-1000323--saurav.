import streamlit as st
import google.generativeai as genai
import pandas as pd

# ==========================================
# 1. Page Configuration & Setup
# ==========================================
# MUST be the first Streamlit command
st.set_page_config(page_title="AuraFit AI", page_icon="⚡", layout="wide")

# Securely fetch the API key from Streamlit Secrets
API_KEY = st.secrets.get("GEMINI_API_KEY")

if not API_KEY:
    st.error("⚠️ Gemini API Key missing. Please set 'GEMINI_API_KEY' in your Streamlit Secrets vault.")
    st.stop()

genai.configure(api_key=API_KEY)

# Initialize Session States to remember user data across tab clicks
if 'outdoor_mode' not in st.session_state: st.session_state.outdoor_mode = False
if 'ai_plan' not in st.session_state: st.session_state.ai_plan = None
if 'current_feature' not in st.session_state: st.session_state.current_feature = None
if 'diet_plan' not in st.session_state: st.session_state.diet_plan = None
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'workout_calendar' not in st.session_state: st.session_state.workout_calendar = None
if 'help_response' not in st.session_state: st.session_state.help_response = None
if 'quick_prompts' not in st.session_state: st.session_state.quick_prompts = None

# Remember sidebar inputs
for key in ['sport', 'position', 'injuries', 'prefs', 'nutrition', 'calories', 'goal']:
    if key not in st.session_state:
        st.session_state[key] = ""

# ==========================================
# 2. AI Logic & API Call Functions
# ==========================================
FEATURES = {
    "Full-body workout plan": "Create a detailed full-body workout plan tailored for the specific sport and position.",
    "Safe recovery training schedule": "Design a safe, structured recovery training schedule that carefully adapts to the listed injuries and risk zones.",
    "Tactical coaching tips": "Provide actionable tactical coaching tips to improve position-specific skills and game intelligence.",
    "Personalized warm-up and cooldown": "Design a personalized, dynamic warm-up and static cooldown routine specific to the sport.",
    "Mental focus & visualization": "Provide a mental focus and pre-match visualization routine to build confidence and game readiness.",
    "Hydration strategy plan": "Outline a precise hydration and electrolyte strategy plan for pre, during, and post-activity.",
    "Positional decision-making drills": "Suggest specific, situational decision-making drills tailored to the player's position.",
    "Post-injury mobility workouts": "Design gentle, effective mobility workouts strictly tailored for post-injury recovery and joint health.",
    "Tournament stamina routines": "Provide progressive stamina-building cardiovascular and muscular endurance routines."
}

def get_temperature(feature_name):
    creative_features = ["Tactical coaching tips", "Mental focus & visualization", "Positional decision-making drills"]
    return 0.8 if feature_name in creative_features else 0.3

def generate_diet_plan(sport, position, goal, nutrition, calories):
    try:
        prompt = f"Athlete: {sport}, {position}. Goal: {goal}. Diet: {nutrition}. Calories: {calories}.\nProvide a highly structured, week-long sports nutrition guide respecting these exact dietary needs. Format with clean markdown."
        model = genai.GenerativeModel("gemini-1.5-flash", system_instruction="Safety-conscious, high-performance sports nutritionist.")
        response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=0.3))
        return response.text
    except Exception as e:
        return f"🚨 API Error: {str(e)}"

def generate_quick_prompts(sport):
    try:
        prompt = f"Provide exactly 5 unique, highly specific single-sentence prompt suggestions a {sport} player could ask their AI coach. Format as a simple bulleted list."
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=0.7))
        return response.text
    except Exception as e:
        return f"🚨 API Error: {str(e)}"

def generate_calendar(sport, position, goal):
    try:
        prompt = f"Structure a 7-day high-level workout calendar for a {sport} player ({position}) focusing on {goal}. Provide a markdown table with columns: Day (Mon-Sun), Core Workout, Sport-Specific Drill, Nutrition Note. Include necessary rest days."
        model = genai.GenerativeModel("gemini-1.5-flash", system_instruction="Professional sports coach scheduling safe training weeks.")
        response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=0.3))
        return response.text
    except Exception as e:
        return f"🚨 API Error: {str(e)}"

def generate_help(query, sport):
    try:
        prompt = f"Provide immediate, step-by-step first aid or safety tips for: '{query}' in the context of {sport}. State clearly you are not a doctor. List red-flag symptoms requiring a 911 call. Format with clear bullet points."
        model = genai.GenerativeModel("gemini-1.5-flash", system_instruction="Strict, precise, safety-first sports first-aid guide.")
        response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=0.1))
        return response.text
    except Exception as e:
        return f"🚨 API Error: {str(e)}"

# ==========================================
# 3. CSS Injection: Clear Glass OS
# ==========================================
# A dark, high-contrast sports background matching your aesthetic
BG_IMAGE = "https://images.unsplash.com/photo-1518063319789-7217e6706b04?q=80&w=2000&auto=format&fit=crop"

def inject_custom_css(is_outdoor_mode):
    if is_outdoor_mode:
        card_bg = "rgba(10, 10, 10, 0.95)"
        border = "2px solid #FFFFFF"
        blur = "blur(0px)"
        text_shadow = "none"
        bg_css = "background-color: #000000;"
    else:
        card_bg = "rgba(255, 255, 255, 0.08)"
        border = "1px solid rgba(255, 255, 255, 0.2)"
        blur = "blur(16px)"
        text_shadow = "0 2px 10px rgba(0,0,0,0.8)"
        bg_css = f"background-image: url('{BG_IMAGE}'); background-size: cover; background-attachment: fixed; background-position: center;"

    css = f"""
    <style>
        .stApp {{ {bg_css} }}
        
        /* Glass Effect for containers */
        .glass-card, div[data-testid="stForm"], div[data-testid="stExpander"] {{
            background: {card_bg} !important;
            backdrop-filter: {blur} !important;
            -webkit-backdrop-filter: {blur} !important;
            border: {border} !important;
            border-radius: 20px !important;
            padding: 20px;
            color: white !important;
            text-shadow: {text_shadow};
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5) !important;
        }}

        /* Inputs and Text Areas */
        .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {{
            background-color: rgba(0, 0, 0, 0.4) !important;
            color: white !important;
            border: 1px solid rgba(255,255,255,0.3) !important;
            border-radius: 10px !important;
        }}

        /* Tabs styling */
        button[data-baseweb="tab"] {{
            background-color: rgba(0,0,0,0.4) !important;
            color: white !important;
            border-radius: 10px 10px 0 0 !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            margin-right: 5px;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            background-color: rgba(0, 255, 170, 0.2) !important;
            border-bottom: 2px solid #00FFAA !important;
            color: #00FFAA !important;
        }}

        /* Chat bubbles */
        .chat-user {{ background: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 15px 15px 0 15px; margin-bottom: 10px; text-align: right; border: 1px solid rgba(255,255,255,0.2); }}
        .chat-coach {{ background: rgba(0, 255, 170, 0.15); padding: 15px; border-radius: 15px 15px 15px 0; margin-bottom: 20px; border: 1px solid rgba(0,255,170,0.3); }}

        /* Typography */
        .glass-title {{ font-size: 1.1rem; color: #ccc; text-transform: uppercase; letter-spacing: 1px; }}
        .glass-metric {{ font-size: 3rem; font-weight: 800; line-height: 1.2; }}
        .cyan {{ color: #00E5FF; text-shadow: 0 0 15px rgba(0, 229, 255, 0.6); }}
        .green {{ color: #00FFAA; text-shadow: 0 0 15px rgba(0, 255, 170, 0.6); }}
        .magenta {{ color: #FF00AA; text-shadow: 0 0 15px rgba(255, 0, 170, 0.6); }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def metric_card(title, value, unit, color_class):
    st.markdown(f"""
    <div class="glass-card" style="text-align: center;">
        <div class="glass-title">{title}</div>
        <div class="glass-metric {color_class}">{value} <span style="font-size: 1.2rem;">{unit}</span></div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 4. User Interface Layout
# ==========================================
col_logo, col_toggle = st.columns([4, 1])
with col_logo:
    st.markdown("<h1 style='color: white; text-shadow: 0 2px 10px #000;'>⚡ AURAFIT OS</h1>", unsafe_allow_html=True)
with col_toggle:
    st.session_state.outdoor_mode = st.toggle("☀️ Outdoor Mode", value=st.session_state.outdoor_mode)

inject_custom_css(st.session_state.outdoor_mode)

# --- SIDEBAR ---
st.sidebar.markdown("<h2 style='color: white;'>📋 Athlete Profile</h2>", unsafe_allow_html=True)
with st.sidebar.form("profile_form"):
    st.session_state.sport = st.text_input("Sport", value=st.session_state.sport, placeholder="e.g., Basketball")
    st.session_state.position = st.text_input("Position", value=st.session_state.position, placeholder="e.g., Point Guard")
    st.session_state.injuries = st.text_input("Injuries / Risks", value=st.session_state.injuries)
    st.session_state.prefs = st.text_input("Training Prefs", value=st.session_state.prefs)
    st.session_state.nutrition = st.text_input("Diet (Veg/Allergies)", value=st.session_state.nutrition)
    st.session_state.calories = st.text_input("Calorie Goal", value=st.session_state.calories)
    st.session_state.goal = st.text_input("Primary Goal", value=st.session_state.goal)
    
    st.markdown("---")
    selected_feature = st.selectbox("Playbook Focus:", list(FEATURES.keys()))
    if st.form_submit_button("GENERATE PLAYBOOK 🚀"):
        if st.session_state.sport and st.session_state.position:
            with st.spinner("Drafting Playbook..."):
                ctx = f"Sport: {st.session_state.sport}, Pos: {st.session_state.position}, Injuries: {st.session_state.injuries}, Goal: {st.session_state.goal}"
                prompt = f"{ctx}\n\nTask: {FEATURES[selected_feature]}"
                model = genai.GenerativeModel("gemini-1.5-flash", system_instruction="Encouraging, safety-conscious professional coach.")
                res = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=get_temperature(selected_feature)))
                st.session_state.ai_plan = res.text
                st.session_state.current_feature = selected_feature
        else:
            st.error("Sport and Position required!")

# Sidebar Quick Prompts
if st.sidebar.button("💡 Get Quick Prompts"):
    if st.session_state.sport:
        with st.spinner("Thinking..."):
            st.session_state.quick_prompts = generate_quick_prompts(st.session_state.sport)
    else:
        st.sidebar.warning("Enter your sport first.")

if st.session_state.quick_prompts:
    st.sidebar.markdown(f"<div class='glass-card' style='padding: 10px; font-size: 0.9em;'>{st.session_state.quick_prompts}</div>", unsafe_allow_html=True)


# --- MAIN TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 Vitals", "🤖 Playbook & Diet", "💬 Chat", "📅 Calendar", "⚠️ Help"])

with tab1:
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: metric_card("Heart Rate", "112", "bpm", "magenta")
    with c2: metric_card("Active Energy", "1,240", "kcal", "green")
    with c3: metric_card("Readiness", "88", "%", "cyan")

with tab2:
    st.markdown("<br>", unsafe_allow_html=True)
    c_play, c_diet = st.columns(2)
    
    with c_play:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        if st.session_state.ai_plan:
            st.markdown(f"<h3 style='color:#00FFAA;'>{st.session_state.current_feature}</h3>", unsafe_allow_html=True)
            st.markdown(st.session_state.ai_plan)
        else:
            st.markdown("<h3>No Playbook Yet</h3><p>Fill out sidebar and click Generate.</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c_diet:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#00FFAA;'>🥦 Diet Plan</h3>", unsafe_allow_html=True)
        if st.button("Generate Diet Plan"):
            if st.session_state.sport and st.session_state.nutrition:
                with st.spinner("Cooking up your diet plan..."):
                    st.session_state.diet_plan = generate_diet_plan(
                        st.session_state.sport, st.session_state.position, st.session_state.goal, 
                        st.session_state.nutrition, st.session_state.calories
                    )
            else:
                st.warning("Ensure Sport and Diet fields are filled in the sidebar.")
        
        if st.session_state.diet_plan:
            st.markdown(st.session_state.diet_plan)
        st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    st.markdown("<br><div class='glass-card'><h3 style='color:#00FFAA;'>💬 Coach Chat</h3>", unsafe_allow_html=True)
    
    # Display Chat History
    for msg in st.session_state.chat_history:
        css_class = "chat-user" if msg['role'] == 'user' else "chat-coach"
        st.markdown(f"<div class='{css_class}'>{msg['text']}</div>", unsafe_allow_html=True)
        
    # Chat Input
    with st.form("chat_form", clear_on_submit=True):
        col_input, col_btn = st.columns([5, 1])
        with col_input:
            user_msg = st.text_input("Ask CoachBot:")
        with col_btn:
            submitted = st.form_submit_button("Send 哨")
            
        if submitted and user_msg:
            st.session_state.chat_history.append({"role": "user", "text": user_msg})
            with st.spinner("Coach is typing..."):
                ctx = f"Context: {st.session_state.sport} player. Query: {user_msg}"
                model = genai.GenerativeModel("gemini-1.5-flash", system_instruction="Brief, encouraging sports coach.")
                res = model.generate_content(ctx)
                st.session_state.chat_history.append({"role": "coach", "text": res.text})
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

with tab4:
    st.markdown("<br><div class='glass-card'><h3 style='color:#00FFAA;'>📅 Weekly Calendar</h3>", unsafe_allow_html=True)
    if st.button("Generate Weekly Calendar"):
        if st.session_state.sport:
            with st.spinner("Scheduling..."):
                st.session_state.workout_calendar = generate_calendar(st.session_state.sport, st.session_state.position, st.session_state.goal)
        else:
            st.warning("Sport required in sidebar.")
            
    if st.session_state.workout_calendar:
        st.markdown(st.session_state.workout_calendar)
    st.markdown("</div>", unsafe_allow_html=True)

with tab5:
    st.markdown("<br><div class='glass-card'><h3 style='color:#FF00AA;'>⚠️ Emergency & First Aid</h3>", unsafe_allow_html=True)
    help_query = st.text_input("What happened?", placeholder="e.g. Rolled ankle, Dislocated shoulder")
    if st.button("Get Safe Guidance"):
        if help_query and st.session_state.sport:
            with st.spinner("Finding safety protocols..."):
                st.session_state.help_response = generate_help(help_query, st.session_state.sport)
        else:
            st.warning("Enter an injury and ensure your sport is in the sidebar.")
            
    if st.session_state.help_response:
        st.markdown(st.session_state.help_response)
    st.markdown("</div>", unsafe_allow_html=True)
