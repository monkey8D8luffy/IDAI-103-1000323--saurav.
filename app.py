import streamlit as st
import google.generativeai as genai
import pandas as pd
import numpy as np

# ==========================================
# 1. Page Configuration & Setup
# ==========================================
# Must be the first Streamlit command
st.set_page_config(page_title="NextGen Sports Lab", page_icon="⚡", layout="wide")

# Securely fetch the API key from Streamlit Secrets
API_KEY = st.secrets.get("GEMINI_API_KEY")

if not API_KEY:
    st.error("⚠️ **NextGen Sports Lab Critical System Error**")
    st.markdown("""
    Your **Gemini API Key is missing**. The AI Coach cannot operate without it.
    
    ### How to solve this immediately:
    1.  If you are running this on Streamlit Cloud, go to your dashboard, click the **three vertical dots (⋮)** next to this app, and select **Settings** -> **Secrets**.
    2.  Paste exactly this and click Save (keeping the quotation marks!):
        ```toml
        GEMINI_API_KEY = "your-actual-api-key-from-google"
        ```
    3.  Refresh the application.
    """)
    st.stop()

genai.configure(api_key=API_KEY)

# Initialize Session States to remember user data across interactions
if 'outdoor_mode' not in st.session_state: st.session_state.outdoor_mode = False
if 'ai_plan' not in st.session_state: st.session_state.ai_plan = None
if 'current_feature' not in st.session_state: st.session_state.current_feature = None
if 'diet_plan' not in st.session_state: st.session_state.diet_plan = None
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'workout_calendar' not in st.session_state: st.session_state.workout_calendar = None
if 'help_response' not in st.session_state: st.session_state.help_response = None
if 'quick_prompts_list' not in st.session_state: st.session_state.quick_prompts_list = []

# Remember sidebar inputs
for key in ['sport', 'position', 'injuries', 'prefs', 'nutrition', 'calories', 'goal']:
    if key not in st.session_state:
        st.session_state[key] = ""

# ==========================================
# 2. AI Logic & API Call Functions
# ==========================================
FEATURES = {
    "Workout Plan": "Create a detailed full-body workout plan tailored for the specific sport and position.",
    "Recovery Schedule": "Design a safe, structured recovery training schedule that carefully adapts to the listed injuries and risk zones.",
    "Tactical Tips": "Provide actionable tactical coaching tips to improve position-specific skills and game intelligence.",
    "Warm-up & Cooldown": "Design a personalized, dynamic warm-up and static cooldown routine specific to the sport.",
    "Mental Focus Routine": "Provide a mental focus and pre-match visualization routine to build confidence and game readiness.",
    "Hydration Strategy": "Outline a precise hydration and electrolyte strategy plan for pre, during, and post-activity.",
    "Decision-making Drills": "Suggest specific, situational decision-making drills tailored to the player's position.",
    "Mobility Workouts": "Design gentle, effective mobility workouts strictly tailored for post-injury recovery and joint health.",
    "Tournament Stamina": "Provide progressive stamina-building cardiovascular and muscular endurance routines."
}

def get_temperature(feature_name):
    # Safety-critical features get low temperature; tactical ones get higher
    creative_features = ["Tactical Tips", "Mental Focus Routine", "Decision-making Drills"]
    return 0.8 if feature_name in creative_features else 0.3

def generate_diet_plan(sport, position, goal, nutrition, calories):
    try:
        prompt = f"Athlete: {sport}, {position}. Goal: {goal}. Diet: {nutrition}. Calories: {calories}.\nProvide a highly structured, week-long sports nutrition guide respecting these exact dietary needs. Format with clean markdown."
        model = genai.GenerativeModel("gemini-1.5-flash", system_instruction="Safety-conscious, high-performance sports nutritionist.")
        response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=0.3))
        return response.text
    except Exception as e:
        return f"🚨 API Error: {str(e)}"

# We use @st.cache_data to make this dynamic to the sport but efficient
@st.cache_data(show_spinner=False)
def generate_quick_prompts(sport):
    try:
        sport_context = sport if sport else "general fitness"
        prompt = f"Write exactly 4 short, highly specific, single-sentence prompt suggestions that a {sport_context} player would ask an AI sports coach. Separate each prompt with a pipe character '|'."
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=0.8))
        prompts = [p.strip() for p in response.text.split('|') if p.strip()]
        return prompts[:4] # Ensure we only get 4
    except:
        return ["Design a 20-minute HIIT warm-up.", "How can I improve my reaction time?", "Give me a post-workout recovery routine.", "What should I eat before a big match?"]

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
        prompt = f"Provide immediate, step-by-step first aid or safety tips for handling the problem: '{query}' in the context of {sport}. State clearly you are not a doctor. List red-flag symptoms requiring a 911 call. Format with clear bullet points."
        model = genai.GenerativeModel("gemini-1.5-flash", system_instruction="Strict, precise, safety-first sports first-aid guide.")
        response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=0.1))
        return response.text
    except Exception as e:
        return f"🚨 API Error: {str(e)}"

def process_chat(user_msg):
    st.session_state.chat_history.append({"role": "user", "text": user_msg})
    
    ctx = f"Athlete Profile: {st.session_state.sport} ({st.session_state.position}). Goal: {st.session_state.goal}. Injuries: {st.session_state.injuries}."
    model = genai.GenerativeModel("gemini-1.5-flash", system_instruction="You are a brief, encouraging, and highly professional sports coach. Prioritize safe form and actionable advice.")
    
    # Passing context + query to model
    full_prompt = f"{ctx}\n\nUser: {user_msg}"
    response = model.generate_content(full_prompt)
    
    st.session_state.chat_history.append({"role": "coach", "text": response.text})

# ==========================================
# 3. CSS Injection: The B&W "Glass OS"
# ==========================================
# A grayscale photograph of a modern angular concrete gymnasium
BG_IMAGE = "https://images.unsplash.com/photo-1547941126-3d5322b218b0?q=80&w=2000&auto=format&fit=crop"

def inject_custom_css(is_outdoor_mode):
    if is_outdoor_mode:
        card_bg = "rgba(10, 10, 10, 0.95)"
        border = "2px solid #FFFFFF"
        blur = "blur(0px)"
        text_shadow = "none"
        bg_css = "background-color: #000000;"
    else:
        # High-contrast B&W Clear Glassmorphism Mode
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
            padding: 12px !important;
            font-size: 1.1rem !important;
        }}

        /* Prompt Buttons */
        .stButton button {{
            background-color: rgba(0, 0, 0, 0.4) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 12px !important;
            color: #FFFFFF !important;
            transition: all 0.2s;
            width: 100%;
            height: 100%;
            text-align: left;
            padding: 15px !important;
        }}
        .stButton button:hover {{
            background-color: rgba(255, 255, 255, 0.15) !important;
            border-color: #FFFFFF !important;
        }}

        /* Tabs styling over glass */
        button[data-baseweb="tab"] {{
            background-color: rgba(0,0,0,0.4) !important;
            color: white !important;
            border-radius: 10px 10px 0 0 !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            margin-right: 5px;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            background-color: rgba(255, 255, 255, 0.15) !important;
            border-bottom: 2px solid #FFFFFF !important;
            color: #FFFFFF !important;
        }}

        /* Chat bubbles (B&W) */
        .chat-user {{ background: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 15px 15px 0 15px; margin-bottom: 10px; text-align: right; border: 1px solid rgba(255,255,255,0.2); }}
        .chat-coach {{ background: rgba(255, 255, 255, 0.03); padding: 15px; border-radius: 15px 15px 15px 0; margin-bottom: 20px; border: 1px solid rgba(255,255,255,0.1); }}

    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# ==========================================
# 4. User Interface Layout
# ==========================================
col_logo, col_toggle = st.columns([4, 1])
with col_logo:
    st.markdown("<h1 style='color: white; text-shadow: 0 2px 10px #000;'>⚡ NEXTGEN SPORTS LAB</h1>", unsafe_allow_html=True)
with col_toggle:
    st.session_state.outdoor_mode = st.toggle("☀️ Outdoor Mode", value=st.session_state.outdoor_mode)

inject_custom_css(st.session_state.outdoor_mode)

# --- SIDEBAR (Profile Form) ---
st.sidebar.markdown("<h2 style='color: white;'>📋 Athlete Profile</h2>", unsafe_allow_html=True)
with st.sidebar.form("profile_form"):
    st.session_state.sport = st.text_input("Sport", value=st.session_state.sport, placeholder="e.g., Basketball")
    st.session_state.position = st.text_input("Position", value=st.session_state.position, placeholder="e.g., Point Guard")
    st.session_state.injuries = st.text_input("Injuries / Risks", value=st.session_state.injuries)
    st.session_state.prefs = st.text_input("Training Prefs", value=st.session_state.prefs)
    st.session_state.nutrition = st.text_input("Diet (Veg/Allergies)", value=st.session_state.nutrition)
    st.session_state.calories = st.text_input("Calorie Goal", value=st.session_state.calories)
    st.session_state.goal = st.text_input("Primary Goal", value=st.session_state.goal)
    st.form_submit_button("Save Profile Data")

# --- MAIN TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["💬 AI Coach", "🤖 Playbook & Diet", "📅 Calendar", "⚠️ Help"])

# ------------------------------------------
# TAB 1: Chatbot & Home Interface
# ------------------------------------------
with tab1:
    st.markdown("<br>", unsafe_allow_html=True)
    
    # HOME INTERFACE (No chat history yet)
    if len(st.session_state.chat_history) == 0:
        st.markdown("<h2 style='text-align: center; color: white; margin-bottom: 30px;'>What are we training today?</h2>", unsafe_allow_html=True)
        
        # Central Search Form
        with st.form("home_search_form", clear_on_submit=True):
            col_search, col_send = st.columns([6, 1])
            with col_search:
                user_msg = st.text_input("Message CoachBot...", label_visibility="collapsed", placeholder="Ask a question, request a drill, or generate a playbook...")
            with col_send:
                submitted = st.form_submit_button("Send 哨", use_container_width=True)
            
            if submitted and user_msg:
                with st.spinner("Analyzing..."):
                    process_chat(user_msg)
                st.rerun()

        # Dynamic Prompt Recommendations
        st.markdown("<br><p style='text-align: center; color: #ccc;'>💡 <b>NextGen Prompts</b></p>", unsafe_allow_html=True)
        prompts = generate_quick_prompts(st.session_state.sport)
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            if st.button(prompts[0], key="p1"): 
                process_chat(prompts[0]); st.rerun()
            if st.button(prompts[1], key="p2"): 
                process_chat(prompts[1]); st.rerun()
        with col_p2:
            if st.button(prompts[2], key="p3"): 
                process_chat(prompts[2]); st.rerun()
            if len(prompts) > 3 and st.button(prompts[3], key="p4"): 
                process_chat(prompts[3]); st.rerun()

    # ACTIVE CHAT INTERFACE
    else:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        
        # Display Chat History
        for msg in st.session_state.chat_history:
            css_class = "chat-user" if msg['role'] == 'user' else "chat-coach"
            st.markdown(f"<div class='{css_class}'>{msg['text']}</div>", unsafe_allow_html=True)
            
        # Unified chat input anchored at bottom of thread
        with st.form("active_chat_form", clear_on_submit=True):
            col_input, col_btn = st.columns([5, 1])
            with col_input:
                user_msg = st.text_input("Reply to CoachBot...", label_visibility="collapsed")
            with col_btn:
                submitted = st.form_submit_button("Send 哨")
                
            if submitted and user_msg:
                with st.spinner("Coach is typing..."):
                    process_chat(user_msg)
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------
# TAB 2: Playbook & Diet
# ------------------------------------------
with tab2:
    st.markdown("<br>", unsafe_allow_html=True)
    c_play, c_diet = st.columns(2)
    
    with c_play:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#FFFFFF;'>🤖 Auto-Playbook</h3>", unsafe_allow_html=True)
        selected_feature = st.selectbox("Select Playbook Focus:", list(FEATURES.keys()))
        if st.button("Generate Selected Playbook"):
            if st.session_state.sport:
                with st.spinner("Drafting Playbook..."):
                    ctx = f"Sport: {st.session_state.sport}, Pos: {st.session_state.position}, Injuries: {st.session_state.injuries}, Goal: {st.session_state.goal}"
                    prompt = f"{ctx}\n\nTask: {FEATURES[selected_feature]}"
                    model = genai.GenerativeModel("gemini-1.5-flash", system_instruction="Encouraging, safety-conscious professional coach.")
                    res = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=get_temperature(selected_feature)))
                    st.session_state.ai_plan = res.text
                    st.session_state.current_feature = selected_feature
            else:
                st.error("Sport required in sidebar!")
                
        if st.session_state.ai_plan:
            st.markdown("---")
            st.markdown(f"<h4 style='color:#ccc;'>{st.session_state.current_feature}</h4>", unsafe_allow_html=True)
            st.markdown(st.session_state.ai_plan)
        st.markdown("</div>", unsafe_allow_html=True)

    with c_diet:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#FFFFFF;'>🥦 Diet Plan</h3>", unsafe_allow_html=True)
        if st.button("Generate Diet Plan🍽️"):
            if st.session_state.sport and st.session_state.nutrition:
                with st.spinner("Cooking up your diet plan..."):
                    st.session_state.diet_plan = generate_diet_plan(
                        st.session_state.sport, st.session_state.position, st.session_state.goal, 
                        st.session_state.nutrition, st.session_state.calories
                    )
            else:
                st.warning("Ensure Sport and Diet fields are filled in the sidebar.")
        
        if st.session_state.diet_plan:
            st.markdown("---")
            st.markdown(st.session_state.diet_plan)
        st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------
# TAB 3: Calendar
# ------------------------------------------
with tab3:
    st.markdown("<br><div class='glass-card'><h3 style='color:#FFFFFF;'>📅 Weekly Calendar</h3>", unsafe_allow_html=True)
    if st.button("Generate Weekly Calendar🗓️"):
        if st.session_state.sport:
            with st.spinner("Scheduling..."):
                st.session_state.workout_calendar = generate_calendar(st.session_state.sport, st.session_state.position, st.session_state.goal)
        else:
            st.warning("Sport required in sidebar.")
            
    if st.session_state.workout_calendar:
        st.markdown(st.session_state.workout_calendar)
    st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------
# TAB 4: Help & Emergency
# ------------------------------------------
with tab4:
    st.markdown("<br><div class='glass-card'><h3 style='color:#FFFFFF;'>⚠️ Help & First Aid</h3>", unsafe_allow_html=True)
    help_query = st.text_input("What happened?", placeholder="e.g. Rolled ankle, Dehydration symptoms")
    if st.button("Get Safe Guidance"):
        if help_query and st.session_state.sport:
            with st.spinner("Finding safety protocols..."):
                st.session_state.help_response = generate_help(help_query, st.session_state.sport)
        else:
            st.warning("Enter a query and ensure your sport is in the sidebar.")
            
    if st.session_state.help_response:
        st.markdown(st.session_state.help_response)
    st.markdown("</div>", unsafe_allow_html=True)
