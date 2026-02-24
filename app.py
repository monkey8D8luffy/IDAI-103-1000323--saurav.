"""
CoachBot AI - Personalized Sports Coaching powered by Gemini 1.5
=================================================================
A Streamlit web application that generates tailored coaching advice
using the Google Generative AI (Gemini 1.5) API.

Usage:
    streamlit run app.py
"""

import streamlit as st
import google.generativeai as genai

# ──────────────────────────────────────────────────────────────────────────────
# Page Configuration
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CoachBot AI",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# Custom CSS for a clean, sport-inspired look
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700&family=Barlow:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Barlow', sans-serif;
}
h1, h2, h3 {
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 700;
    letter-spacing: 0.5px;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #0f1923 0%, #1a2d3d 100%);
    color: #e8edf2;
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stTextInput label,
[data-testid="stSidebar"] .stTextArea label,
[data-testid="stSidebar"] .stNumberInput label,
[data-testid="stSidebar"] p {
    color: #c8d8e8 !important;
    font-weight: 500;
}
[data-testid="stSidebar"] .stSelectbox > div > div,
[data-testid="stSidebar"] .stTextInput > div > div > input,
[data-testid="stSidebar"] .stTextArea > div > textarea,
[data-testid="stSidebar"] .stNumberInput > div > div > input {
    background-color: #1e3448 !important;
    color: #e8edf2 !important;
    border: 1px solid #2e4a60 !important;
    border-radius: 6px;
}

/* Main header */
.coachbot-header {
    background: linear-gradient(90deg, #0f1923 0%, #1a4a6b 50%, #0f1923 100%);
    border-left: 5px solid #00c6ff;
    padding: 18px 24px;
    border-radius: 8px;
    margin-bottom: 24px;
}
.coachbot-header h1 {
    color: #ffffff;
    margin: 0;
    font-size: 2.4rem;
}
.coachbot-header p {
    color: #8ab4cc;
    margin: 4px 0 0 0;
    font-size: 1.05rem;
}

/* Feature selector card */
.feature-card {
    background: #f0f6fb;
    border: 1px solid #cfe3ef;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 20px;
}

/* Generate button */
div.stButton > button {
    background: linear-gradient(90deg, #005f8a 0%, #007bb5 100%);
    color: white;
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 1.15rem;
    font-weight: 700;
    letter-spacing: 1px;
    padding: 12px 30px;
    border: none;
    border-radius: 8px;
    width: 100%;
    transition: opacity 0.2s;
}
div.stButton > button:hover {
    opacity: 0.88;
}

/* Response area */
.response-box {
    background: #f7fbff;
    border-left: 5px solid #007bb5;
    border-radius: 8px;
    padding: 24px 28px;
    margin-top: 20px;
    line-height: 1.75;
}

/* Temperature badge */
.temp-badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    margin-left: 8px;
    vertical-align: middle;
}
.temp-conservative { background: #d4edda; color: #155724; }
.temp-creative     { background: #fff3cd; color: #856404; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# Constants & Feature Definitions
# ──────────────────────────────────────────────────────────────────────────────

# Mapping of feature name → (display label, temperature category)
# temperature categories:
#   "conservative" → 0.3  (workouts, recovery, injuries)
#   "creative"     → 0.8  (tactical, mental, nutrition)
FEATURES: dict[str, tuple[str, str]] = {
    "full_body_workout":       ("💪 Full-Body Workout Plan",                "conservative"),
    "safe_recovery":           ("🩹 Safe Recovery Training Schedule",        "conservative"),
    "tactical_tips":           ("🎯 Tactical Coaching Tips",                 "creative"),
    "nutrition_guide":         ("🥗 Week-Long Nutrition Guide",              "creative"),
    "warmup_cooldown":         ("🔥 Personalised Warm-Up & Cooldown Routine","conservative"),
    "mental_focus":            ("🧘 Mental Focus & Visualisation Routine",   "creative"),
    "hydration_strategy":      ("💧 Hydration & Electrolyte Strategy",       "conservative"),
    "decision_drills":         ("⚡ Positional Decision-Making Drills",      "conservative"),
    "mobility_recovery":       ("🦵 Mobility Workouts for Post-Injury",      "conservative"),
    "stamina_tournament":      ("🏅 Stamina-Building for Tournament Prep",   "conservative"),
}

TEMPERATURE_MAP = {"conservative": 0.3, "creative": 0.8}

# ──────────────────────────────────────────────────────────────────────────────
# System Persona
# ──────────────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "You are CoachBot AI — a professional youth sports coach with expertise in "
    "physiology, sports science, nutrition, and sports psychology. "
    "Always speak in an encouraging, informative, and safety-conscious tone. "
    "Prioritise athlete wellbeing; include safety warnings when relevant. "
    "Use clear headings, bullet points, and numbered lists to keep advice "
    "easy to follow. Never suggest actions that could aggravate existing injuries."
)

# ──────────────────────────────────────────────────────────────────────────────
# Prompt Templates
# ──────────────────────────────────────────────────────────────────────────────

def build_prompt(feature_key: str, inputs: dict) -> str:
    """
    Build a detailed, context-rich prompt by combining the chosen feature
    template with the user's personal inputs.
    """
    s = inputs  # shorthand

    # Shared context block injected into every prompt
    context = (
        f"Athlete Profile:\n"
        f"- Sport: {s['sport']}\n"
        f"- Position: {s['position']}\n"
        f"- Injury History / Risk Zones: {s['injuries'] or 'None reported'}\n"
        f"- Training Preferences: Intensity = {s['intensity']}, Style = {s['style']}\n"
        f"- Nutrition: {s['diet']}, Allergies = {s['allergies'] or 'None'}, "
        f"  Daily Calorie Target = {s['calories']} kcal\n"
        f"- Desired Goal: {s['goal']}\n\n"
    )

    templates = {
        "full_body_workout": (
            f"{context}"
            f"Create a comprehensive 5-day full-body workout plan tailored specifically "
            f"for a {s['position']} in {s['sport']}. "
            f"Ensure exercises strengthen the muscles most used in that position, "
            f"match the {s['intensity']} intensity preference, and avoid stressing "
            f"the injury risk zones: {s['injuries'] or 'N/A'}. "
            f"Include sets, reps, rest periods, and coaching cues for each exercise."
        ),
        "safe_recovery": (
            f"{context}"
            f"Design a safe, structured 2-week recovery training schedule that accounts "
            f"for the athlete's injury history in the following areas: {s['injuries'] or 'N/A'}. "
            f"Include active recovery days, physiotherapy-style exercises, load management "
            f"guidelines, and clear red-flag signals that mean the athlete should stop "
            f"and rest immediately."
        ),
        "tactical_tips": (
            f"{context}"
            f"Provide 10 advanced, position-specific tactical coaching tips for a "
            f"{s['position']} in {s['sport']}. For each tip, explain the concept, "
            f"give a real-game scenario, and describe a drill or mental cue to practise it. "
            f"Align tips with the athlete's goal: {s['goal']}."
        ),
        "nutrition_guide": (
            f"{context}"
            f"Create a detailed 7-day nutrition plan. Each day should include breakfast, "
            f"mid-morning snack, lunch, pre-workout meal, post-workout meal, dinner, and "
            f"an evening snack. Respect these constraints: {s['diet']} diet, "
            f"allergies to {s['allergies'] or 'none'}, aiming for ~{s['calories']} kcal/day. "
            f"Include macronutrient breakdown (protein/carbs/fats) for each day and explain "
            f"how the plan supports the goal: {s['goal']}."
        ),
        "warmup_cooldown": (
            f"{context}"
            f"Design a science-backed, sport-specific warm-up (10–15 min) and cooldown "
            f"(10 min) routine for a {s['position']} in {s['sport']}. "
            f"The warm-up should include dynamic mobility, activation drills, and CNS "
            f"priming. The cooldown should include static stretching and breathing exercises. "
            f"Avoid movements that stress: {s['injuries'] or 'N/A'}."
        ),
        "mental_focus": (
            f"{context}"
            f"Create a personalised 20-minute pre-match mental preparation routine. "
            f"Include: a guided visualisation script tailored to the role of a "
            f"{s['position']} in {s['sport']}, self-talk affirmations, a focus-cue "
            f"keyword strategy, and a breathing protocol. "
            f"Also provide a 5-minute reset routine for use during half-time or breaks."
        ),
        "hydration_strategy": (
            f"{context}"
            f"Develop a precise hydration and electrolyte strategy for a {s['sport']} "
            f"player at {s['intensity']} training intensity. Include: pre-training hydration "
            f"protocol, during-session fluid intake guidelines (ml per hour), electrolyte "
            f"replenishment recommendations, post-session rehydration plan, and signs of "
            f"dehydration to watch for. Tailor advice to goal: {s['goal']}."
        ),
        "decision_drills": (
            f"{context}"
            f"Design 8 positional decision-making drills specifically for a {s['position']} "
            f"in {s['sport']}. For each drill: describe the setup, the decision cues the "
            f"athlete must read, common mistakes, and a progression to increase difficulty. "
            f"Ensure drills are safe given injury history: {s['injuries'] or 'N/A'}."
        ),
        "mobility_recovery": (
            f"{context}"
            f"Create a 4-week progressive mobility and flexibility programme to support "
            f"post-injury recovery, specifically targeting: {s['injuries'] or 'general maintenance'}. "
            f"Week by week, increase range-of-motion demands safely. Include exercise names, "
            f"duration, sets, and clear instructions. Flag any exercises that must be "
            f"approved by a physiotherapist before attempting."
        ),
        "stamina_tournament": (
            f"{context}"
            f"Build an 8-week stamina and endurance programme to prepare a {s['position']} "
            f"in {s['sport']} for tournament competition. Include aerobic base building, "
            f"sport-specific conditioning, interval training, and taper week. "
            f"Match the {s['intensity']} training style preference and protect the "
            f"injury risk zones: {s['injuries'] or 'N/A'}. Tie the plan to goal: {s['goal']}."
        ),
    }

    return templates[feature_key]


# ──────────────────────────────────────────────────────────────────────────────
# Gemini API Helper
# ──────────────────────────────────────────────────────────────────────────────

def call_gemini(prompt: str, temperature: float, api_key: str) -> str:
    """
    Call the Gemini 1.5 Flash model with the given prompt and temperature.
    Returns the generated text or raises an exception on failure.
    """
    genai.configure(api_key=api_key)

    generation_config = genai.types.GenerationConfig(
        temperature=temperature,
        max_output_tokens=2048,
        top_p=0.95,
    )

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
        system_instruction=SYSTEM_PROMPT,
    )

    response = model.generate_content(prompt)
    return response.text


# ──────────────────────────────────────────────────────────────────────────────
# Sidebar — User Inputs
# ──────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚙️ Athlete Profile")
    st.markdown("---")

    api_key = st.text_input(
        "🔑 Gemini API Key",
        type="password",
        help="Get your free key at https://aistudio.google.com",
        placeholder="AIza...",
    )

    st.markdown("### 🏟️ Sport & Position")
    sport = st.text_input("Sport", placeholder="e.g. Football, Basketball, Tennis")
    position = st.text_input("Player Position", placeholder="e.g. Centre-Back, Point Guard")

    st.markdown("### 🩺 Health & Training")
    injuries = st.text_area(
        "Injury History / Risk Zones",
        placeholder="e.g. Left knee ACL (recovered), lower back tightness",
        height=90,
    )
    intensity = st.select_slider(
        "Training Intensity",
        options=["Light", "Moderate", "High", "Elite"],
        value="Moderate",
    )
    style = st.selectbox(
        "Training Style",
        ["Strength-focused", "Endurance-focused", "Skills & Technique",
         "Mixed / Balanced", "Speed & Agility"],
    )

    st.markdown("### 🥗 Nutrition")
    diet = st.selectbox("Dietary Preference", ["Non-Vegetarian", "Vegetarian", "Vegan", "Pescatarian"])
    allergies = st.text_input("Allergies / Intolerances", placeholder="e.g. Gluten, Lactose")
    calories = st.number_input("Daily Calorie Target (kcal)", min_value=1200, max_value=6000,
                               value=2500, step=100)

    st.markdown("### 🎯 Goal")
    goal = st.text_area(
        "Desired Goal",
        placeholder="e.g. Improve speed and reduce injury re-occurrence before the season",
        height=80,
    )

# ──────────────────────────────────────────────────────────────────────────────
# Main Area
# ──────────────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="coachbot-header">
    <h1>🏆 CoachBot AI</h1>
    <p>Your personal AI sports coach — powered by Gemini 1.5</p>
</div>
""", unsafe_allow_html=True)

# Feature Selector
st.markdown('<div class="feature-card">', unsafe_allow_html=True)
st.markdown("### 📋 Select a Coaching Feature")

feature_labels = {k: v[0] for k, v in FEATURES.items()}
selected_key = st.selectbox(
    "Choose what you'd like help with today:",
    options=list(feature_labels.keys()),
    format_func=lambda k: feature_labels[k],
    label_visibility="collapsed",
)

# Show temperature info
selected_category = FEATURES[selected_key][1]
temp_value = TEMPERATURE_MAP[selected_category]
badge_class = "temp-conservative" if selected_category == "conservative" else "temp-creative"
badge_label = f"Temperature: {temp_value} — {'Conservative & Safe' if selected_category == 'conservative' else 'Creative & Expansive'}"

st.markdown(
    f"<small>AI setting: <span class='temp-badge {badge_class}'>{badge_label}</span></small>",
    unsafe_allow_html=True,
)
st.markdown('</div>', unsafe_allow_html=True)

# Generate Button
generate_clicked = st.button("🚀 Generate Coaching Advice", use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# Generation Logic & Output
# ──────────────────────────────────────────────────────────────────────────────

if generate_clicked:
    # ── Validation ──────────────────────────────────────────────────────────
    errors = []
    if not api_key:
        errors.append("🔑 **API Key** is required. Please enter it in the sidebar.")
    if not sport:
        errors.append("🏟️ **Sport** is required.")
    if not position:
        errors.append("📍 **Player Position** is required.")
    if not goal:
        errors.append("🎯 **Desired Goal** is required.")

    if errors:
        st.error("Please fix the following before generating:")
        for e in errors:
            st.markdown(f"- {e}")
        st.stop()

    # ── Build Inputs Dict ────────────────────────────────────────────────────
    user_inputs = {
        "sport": sport,
        "position": position,
        "injuries": injuries,
        "intensity": intensity,
        "style": style,
        "diet": diet,
        "allergies": allergies,
        "calories": calories,
        "goal": goal,
    }

    prompt = build_prompt(selected_key, user_inputs)
    temperature = TEMPERATURE_MAP[selected_category]

    # ── Call Gemini ──────────────────────────────────────────────────────────
    with st.spinner("⏳ CoachBot is crafting your personalised plan..."):
        try:
            result = call_gemini(prompt, temperature, api_key)

            st.success(f"✅ Plan generated for **{feature_labels[selected_key]}**")

            st.markdown('<div class="response-box">', unsafe_allow_html=True)
            st.markdown(result)
            st.markdown('</div>', unsafe_allow_html=True)

            # Download option
            st.download_button(
                label="📥 Download as Text",
                data=result,
                file_name=f"coachbot_{selected_key}.txt",
                mime="text/plain",
            )

        except genai.types.BlockedPromptException:
            st.error(
                "⚠️ The request was blocked by the Gemini safety filters. "
                "Please rephrase your inputs and try again."
            )
        except Exception as exc:
            st.error(f"❌ API Error: {exc}")
            st.info(
                "Common fixes:\n"
                "- Double-check your API key\n"
                "- Ensure the Gemini 1.5 API is enabled in your Google Cloud project\n"
                "- Check your internet connection"
            )

else:
    # Welcome placeholder
    st.info(
        "👈 Fill in your **Athlete Profile** in the sidebar, choose a "
        "**Coaching Feature** above, then hit **Generate** to get started!"
    )
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Coaching Features", "10")
    with col2:
        st.metric("AI Model", "Gemini 1.5")
    with col3:
        st.metric("Personalisation Inputs", "8")
