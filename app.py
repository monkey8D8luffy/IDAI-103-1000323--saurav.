import streamlit as st
import google.generativeai as genai
import pandas as pd
import numpy as np
import base64
import os

# ==========================================
# 1. Page Configuration & Setup
# ==========================================
st.set_page_config(page_title="NextGen Sports Lab", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

API_KEY = st.secrets.get("GEMINI_API_KEY")

if not API_KEY:
    st.error("⚠️ **NextGen Sports Lab Critical System Error**")
    st.markdown("""
    Your **Gemini API Key is missing**. The AI Coach cannot operate without it.
    
    ### How to solve this immediately:
    1.  Go to your Streamlit Cloud dashboard, click the **three vertical dots (⋮)** next to this app, and select **Settings** -> **Secrets**.
    2.  Paste exactly this and click Save:
        ```toml
        GEMINI_API_KEY = "your-actual-api-key-from-google"
        ```
    3.  Refresh the application.
    """)
    st.stop()

genai.configure(api_key=API_KEY)

# Initialize Session States
if 'outdoor_mode' not in st.session_state: st.session_state.outdoor_mode = False
if 'ai_plan' not in st.session_state: st.session_state.ai_plan = None
if 'current_feature' not in st.session_state: st.session_state.current_feature = None
if 'diet_plan' not in st.session_state: st.session_state.diet_plan = None
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'workout_calendar' not in st.session_state: st.session_state.workout_calendar = None
if 'help_response' not in st.session_state: st.session_state.help_response = None

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
    creative_features = ["Tactical Tips", "Mental Focus Routine", "Decision-making Drills"]
    return 0.8 if feature_name in creative_features else 0.3

def generate_diet_plan(sport, position, goal, nutrition, calories):
    try:
        prompt = f"Athlete: {sport}, {position}. Goal: {goal}. Diet: {nutrition}. Calories: {calories}.\nProvide a highly structured, week-long sports nutrition guide respecting these exact dietary needs. Format with clean markdown."
        model = genai.GenerativeModel("gemini-2.5-flash", system_instruction="Safety-conscious, high-performance sports nutritionist.")
        response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=0.3))
        return response.text
    except Exception as e:
        return f"🚨 API Error: {str(e)}"

@st.cache_data(show_spinner=False)
def generate_quick_prompts(sport):
    defaults = [
        "Design a 20-minute HIIT warm-up.", 
        "How can I improve my reaction time?", 
        "Give me a post-workout recovery routine.", 
        "What should I eat before a big match?"
    ]
    try:
        sport_context = sport if sport else "general fitness"
        prompt = f"Write exactly 4 short, highly specific, single-sentence prompt suggestions that a {sport_context} player would ask an AI sports coach. Separate each prompt with a pipe character '|'. No numbers."
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=0.8))
        prompts = [p.strip() for p in response.text.split('|') if p.strip()]
        
        while len(prompts) < 4:
            prompts.append(defaults[len(prompts)])
        return prompts[:4] 
    except:
        return defaults

def generate_calendar(sport, position, goal):
    try:
        prompt = f"Structure a 7-day high-level workout calendar for a {sport} player ({position}) focusing on {goal}. Provide a markdown table with columns: Day (Mon-Sun), Core Workout, Sport-Specific Drill, Nutrition Note. Include necessary rest days."
        model = genai.GenerativeModel("gemini-2.5-flash", system_instruction="Professional sports coach scheduling safe training weeks.")
        response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=0.3))
        return response.text
    except Exception as e:
        return f"🚨 API Error: {str(e)}"

def generate_help(query, sport):
    try:
        prompt = f"Provide immediate, step-by-step first aid or safety tips for handling the problem: '{query}' in the context of {sport}. State clearly you are not a doctor. List red-flag symptoms requiring a 911 call. Format with clear bullet points."
        model = genai.GenerativeModel("gemini-2.5-flash", system_instruction="Strict, precise, safety-first sports first-aid guide.")
        response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=0.1))
        return response.text
    except Exception as e:
        return f"🚨 API Error: {str(e)}"

def process_chat(user_msg):
    st.session_state.chat_history.append({"role": "user", "text": user_msg})
    try:
        ctx = f"Athlete Profile: {st.session_state.sport} ({st.session_state.position}). Goal: {st.session_state.goal}. Injuries: {st.session_state.injuries}."
        model = genai.GenerativeModel("gemini-2.5-flash", system_instruction="You are a brief, encouraging, and highly professional sports coach. Prioritize safe form and actionable advice.")
        
        full_prompt = f"{ctx}\n\nUser: {user_msg}"
        response = model.generate_content(full_prompt)
        st.session_state.chat_history.append({"role": "coach", "text": response.text})
    except Exception as e:
        st.session_state.chat_history.append({"role": "coach", "text": f"🚨 Connection Error: Unable to reach the playbook database. ({str(e)})"})

def handle_prompt_click(prompt_text):
    process_chat(prompt_text)

# ==========================================
# 3. CSS Injection & Smart Background Image Loader
# ==========================================
@st.cache_data
def get_absolute_local_bg():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Actively hunts for ANY image format to bypass renaming errors
        possible_filenames = ['background.jpg', 'background.png', 'background.jpg.png']
        
        for filename in possible_filenames:
            file_path = os.path.join(current_dir, filename)
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    data = f.read()
                # Dynamically set mime type
                mime = "image/png" if "png" in filename.lower() else "image/jpeg"
                return f"url('data:{mime};base64,{base64.b64encode(data).decode()}')"
        return None
    except Exception as e:
        return None

img_bg_css = get_absolute_local_bg() 

def inject_custom_css(is_outdoor_mode, img_url_css):
    if is_outdoor_mode:
        card_bg = "rgba(10, 10, 10, 0.98)"
        border = "2px solid #FFFFFF"
        blur = "blur(0px)"
        text_shadow = "none"
        bg_css = "background-color: #000000 !important;"
    else:
        # High-opacity cards to stand out clearly against the B&W background
        card_bg = "rgba(15, 15, 15, 0.75)"
        border = "1px solid rgba(255, 255, 255, 0.15)"
        blur = "blur(24px)"
        text_shadow = "0 2px 10px rgba(0,0,0,0.9)"
        
        if img_url_css:
            bg_css = f"background-image: {img_url_css} !important; background-size: cover !important; background-attachment: fixed !important; background-position: center !important;"
        else:
            fallback_img = "https://images.unsplash.com/photo-1547941126-3d5322b218b0?q=80&w=2000&auto=format&fit=crop&grayscale"
            bg_css = f"background-image: url('{fallback_img}') !important; background-size: cover !important; background-attachment: fixed !important; background-position: center !important;"

    css = f"""
    <style>
        /* BULLETPROOF BACKGROUND INJECTION */
        [data-testid="stAppViewContainer"] {{
            {bg_css}
        }}
        
        /* Force Streamlit Header to be transparent so it doesn't block the image */
        [data-testid="stHeader"] {{
            background-color: rgba(0, 0, 0, 0) !important;
        }}
        
        /* Adjust layout to match the mockup grid */
        .main .block-container {{
            padding-top: 2rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            max-width: 100% !important;
        }}

        /* HIDE THE NATIVE SLIDER ARROW */
        [data-testid="collapsedControl"] {{ display: none !important; }}
        
        /* STATIC MINIMALIST PILL SIDEBAR */
        [data-testid="stSidebar"] {{
            width: 250px !important;
            min-width: 250px !important;
            max-width: 250px !important;
            background-color: transparent !important;
            border-right: none !important;
        }}
        
        [data-testid="stSidebarUserContent"] {{
            background-color: rgba(10, 10, 10, 0.8) !important;
            backdrop-filter: blur(24px) !important;
            -webkit-backdrop-filter: blur(24px) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 30px !important; /* Exaggerated pill shape */
            margin: 20px 0px 20px 20px !important;
            padding: 30px 15px !important;
            height: calc(100vh - 40px) !important;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.6) !important;
        }}

        /* Format Radio Buttons as Clean Menu Items */
        div[role="radiogroup"] > label > div:first-child {{ display: none; }}
        
        div[role="radiogroup"] > label {{
            background: transparent;
            padding: 12px 15px !important;
            border-radius: 12px;
            margin-bottom: 8px;
            border: 1px solid transparent;
            transition: 0.3s;
            cursor: pointer;
            width: 100% !important;
            display: flex !important;
            align-items: center !important;
        }}
        div[role="radiogroup"] > label:hover {{ background: rgba(255,255,255,0.05); }}
        div[role="radiogroup"] > label[data-checked="true"] {{ 
            background: rgba(255,255,255,0.1); 
            border: 1px solid rgba(255,255,255,0.2);
        }}
        div[role="radiogroup"] p {{ font-size: 1.05rem !important; font-weight: 500; color: white; margin: 0; padding-left: 5px; }}

        /* Glass Cards */
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

        /* Inputs */
        .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {{
            background-color: rgba(0, 0, 0, 0.8) !important;
            color: white !important;
            border: 1px solid rgba(255,255,255,0.2) !important;
            border-radius: 12px !important;
            padding: 12px !important;
            font-size: 1.1rem !important;
        }}

        /* Buttons */
        .stButton button {{
            background-color: rgba(0, 0, 0, 0.8) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 12px !important;
            color: #FFFFFF !important;
            transition: all 0.2s;
            padding: 15px !important;
            white-space: normal !important; 
            height: auto !important; 
        }}
        .stButton button:hover {{
            background-color: rgba(255, 255, 255, 0.1) !important;
            border-color: #FFFFFF !important;
        }}

        /* Chat Bubbles */
        .chat-user {{ 
            background: rgba(40, 40, 40, 0.95); 
            padding: 15px; 
            border-radius: 15px 15px 0 15px; 
            margin-bottom: 10px; 
            text-align: right; 
            border: 1px solid rgba(255,255,255,0.2); 
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        }}
        .chat-coach {{ 
            background: rgba(10, 10, 10, 0.95); 
            padding: 15px; 
            border-radius: 15px 15px 15px 0; 
            margin-bottom: 20px; 
            border: 1px solid rgba(255,255,255,0.1); 
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# ==========================================
# 4. Global Header
# ==========================================
col_logo, col_toggle = st.columns([4, 1])
with col_logo:
    st.markdown("<h1 style='color: white; text-shadow: 0 2px 10px #000; margin-left: 20px;'>⚡ NEXTGEN SPORTS LAB</h1>", unsafe_allow_html=True)
with col_toggle:
    st.session_state.outdoor_mode = st.toggle("☀️ Outdoor Mode", value=st.session_state.outdoor_mode)

inject_custom_css(st.session_state.outdoor_mode, img_bg_css)

# ==========================================
# 5. Fixed Vertical "Floating Pill" Navbar
# ==========================================
st.sidebar.markdown("<br><h3 style='color: white; text-align: center; font-size: 1rem; color: #888;'>SYSTEM MENU</h3><br>", unsafe_allow_html=True)

selected_tab = st.sidebar.radio(
    "Navigation",
    ["💬 AI Coach", "📋 Athlete Profile", "🤖 Playbook & Diet", "📅 Calendar", "⚠️ Help & First Aid"],
    label_visibility="collapsed"
)

# ==========================================
# 6. Content Views
# ==========================================

if selected_tab == "💬 AI Coach":
    if len(st.session_state.chat_history) == 0:
        st.markdown("<br><h2 style='text-align: center; color: white; margin-bottom: 30px; text-shadow: 0 4px 10px #000;'>What are we training today?</h2>", unsafe_allow_html=True)
        
        with st.form("home_search_form", clear_on_submit=True):
            col_search, col_send = st.columns([6, 1])
            with col_search:
                user_msg = st.text_input("Message CoachBot...", label_visibility="collapsed", placeholder="Ask a question, request a drill, or generate a playbook...")
            with col_send:
                submitted = st.form_submit_button("Send 哨", use_container_width=True)
            
            if submitted and user_msg:
                with st.spinner("Analyzing your request..."):
                    process_chat(user_msg)
                st.rerun()

        st.markdown("<br><p style='text-align: center; color: #ccc; text-shadow: 0 2px 5px #000;'>💡 <b>NextGen Prompts</b></p>", unsafe_allow_html=True)
        prompts = generate_quick_prompts(st.session_state.sport)
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.button(prompts[0], key="p1", on_click=handle_prompt_click, args=(prompts[0],), use_container_width=True)
            st.button(prompts[1], key="p2", on_click=handle_prompt_click, args=(prompts[1],), use_container_width=True)
        with col_p2:
            st.button(prompts[2], key="p3", on_click=handle_prompt_click, args=(prompts[2],), use_container_width=True)
            st.button(prompts[3], key="p4", on_click=handle_prompt_click, args=(prompts[3],), use_container_width=True)

    else:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        for msg in st.session_state.chat_history:
            css_class = "chat-user" if msg['role'] == 'user' else "chat-coach"
            st.markdown(f"<div class='{css_class}'>{msg['text']}</div>", unsafe_allow_html=True)
            
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

elif selected_tab == "📋 Athlete Profile":
    st.markdown("<br><div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h2 style='color:#FFFFFF; text-align: center;'>📋 Setup Athlete Profile</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #ccc;'>CoachBot uses this data to generate personalized, safe playbooks.</p><hr>", unsafe_allow_html=True)
    
    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.sport = st.text_input("Sport", value=st.session_state.sport, placeholder="e.g., Basketball")
            st.session_state.injuries = st.text_input("Injuries / Risks", value=st.session_state.injuries, placeholder="e.g., Weak right ankle")
            st.session_state.nutrition = st.text_input("Diet (Veg/Allergies)", value=st.session_state.nutrition, placeholder="e.g., Vegan")
            st.session_state.goal = st.text_input("Primary Goal", value=st.session_state.goal, placeholder="e.g., Increase vertical jump")
        with col2:
            st.session_state.position = st.text_input("Position", value=st.session_state.position, placeholder="e.g., Point Guard")
            st.session_state.prefs = st.text_input("Training Prefs", value=st.session_state.prefs, placeholder="e.g., Prefers bodyweight")
            st.session_state.calories = st.text_input("Calorie Goal", value=st.session_state.calories, placeholder="e.g., 2800 kcal")
            
        st.markdown("<br>", unsafe_allow_html=True)
        if st.form_submit_button("Save Profile Data ✔️", use_container_width=True):
            st.success("✅ Profile Data Saved. CoachBot is calibrated.")
    st.markdown("</div>", unsafe_allow_html=True)

elif selected_tab == "🤖 Playbook & Diet":
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
                    model = genai.GenerativeModel("gemini-2.5-flash", system_instruction="Encouraging, safety-conscious professional coach.")
                    res = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=get_temperature(selected_feature)))
                    st.session_state.ai_plan = res.text
                    st.session_state.current_feature = selected_feature
            else:
                st.error("⚠️ Sport required! Go to 'Athlete Profile' first.")
                
        if st.session_state.ai_plan:
            st.markdown("---")
            st.markdown(f"<h4 style='color:#ccc;'>{st.session_state.current_feature}</h4>", unsafe_allow_html=True)
            st.markdown(st.session_state.ai_plan)
        st.markdown("</div>", unsafe_allow_html=True)

    with c_diet:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#FFFFFF;'>🥦 Diet Plan</h3>", unsafe_allow_html=True)
        if st.button("Generate Diet Plan 🍽️"):
            if st.session_state.sport and st.session_state.nutrition:
                with st.spinner("Cooking up your diet plan..."):
                    st.session_state.diet_plan = generate_diet_plan(
                        st.session_state.sport, st.session_state.position, st.session_state.goal, 
                        st.session_state.nutrition, st.session_state.calories
                    )
            else:
                st.warning("⚠️ Ensure Sport and Diet fields are filled in the 'Athlete Profile' tab.")
        
        if st.session_state.diet_plan:
            st.markdown("---")
            st.markdown(st.session_state.diet_plan)
        st.markdown("</div>", unsafe_allow_html=True)

elif selected_tab == "📅 Calendar":
    st.markdown("<br><div class='glass-card'><h3 style='color:#FFFFFF;'>📅 Weekly Calendar</h3>", unsafe_allow_html=True)
    if st.button("Generate Weekly Calendar 🗓️"):
        if st.session_state.sport:
            with st.spinner("Scheduling..."):
                st.session_state.workout_calendar = generate_calendar(st.session_state.sport, st.session_state.position, st.session_state.goal)
        else:
            st.warning("⚠️ Sport required in the 'Athlete Profile' tab.")
            
    if st.session_state.workout_calendar:
        st.markdown(st.session_state.workout_calendar)
    st.markdown("</div>", unsafe_allow_html=True)

elif selected_tab == "⚠️ Help & First Aid":
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("<h3 style='color:#FFFFFF; text-shadow: 0 2px 5px #000;'>💎 Pre-Made Emergency Protocols</h3>", unsafe_allow_html=True)
    col_em1, col_em2 = st.columns(2)
    
    with col_em1:
        with st.expander("⚠️ Ankle/Joint Sprain (R.I.C.E.)"):
            st.markdown("""
            **1. Rest:** Stop activity immediately. Do not put weight on it.
            **2. Ice:** Apply ice for 15-20 minutes every 2-3 hours.
            **3. Compress:** Wrap with an elastic bandage (not too tight).
            **4. Elevate:** Keep the injured area above the heart to reduce swelling.
            """)
        with st.expander("⚠️ Heat Exhaustion"):
            st.markdown("""
            **Symptoms:** Heavy sweating, cold/pale skin, nausea, dizziness.
            **Action:** - Move to a cool/shaded area immediately.
            - Lie down and elevate legs.
            - Sip cool water or sports drink slowly.
            - Apply cool, wet cloths to the body.
            *Call 911 if vomiting occurs or symptoms worsen after 1 hour.*
            """)
            
    with col_em2:
        with st.expander("⚠️ Concussion Assessment"):
            st.markdown("""
            **Red Flags (Call 911):** Loss of consciousness, vomiting, uneven pupils, worsening headache.
            **Action:**
            - Stop play immediately. Do not return to the game.
            - Keep the athlete calm and still.
            - Ask basic questions (What quarter is it? Who scored last?) to check memory.
            - Have a medical professional clear the athlete before any physical activity.
            """)
        with st.expander("⚠️ Severe Bleeding"):
            st.markdown("""
            **Action:**
            - Apply immediate, firm, direct pressure with a clean cloth or gauze.
            - Maintain pressure without lifting the cloth to check.
            - If blood soaks through, add more cloth on top (do not remove the original).
            - Elevate the injured area above the heart if possible.
            *Call 911 if bleeding does not stop after 10 minutes of pressure.*
            """)

    st.markdown("<br><div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h3 style='color:#FFFFFF;'>🔍 Search Custom Guidance</h3>", unsafe_allow_html=True)
    help_query = st.text_input("Describe the injury or situation:", placeholder="e.g. Dislocated shoulder, Cramp in hamstring")
    
    if st.button("Generate Safe Guidance 🏥"):
        if help_query and st.session_state.sport:
            with st.spinner("Finding safety protocols..."):
                st.session_state.help_response = generate_help(help_query, st.session_state.sport)
        elif not st.session_state.sport:
            st.warning("⚠️ Enter your sport in the 'Athlete Profile' tab for sport-specific advice.")
        else:
            st.warning("⚠️ Enter a query to search.")
            
    if st.session_state.help_response:
        st.markdown("---")
        st.markdown(st.session_state.help_response)
    st.markdown("</div>", unsafe_allow_html=True)
