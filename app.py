"""
CoachBot AI — Smart Fitness Assistance Web App
================================================
Powered by Gemini 1.5 Flash | Built with Streamlit
NextGen Sports Lab · CRS Generative AI Assignment (Scenario 2)

Architecture:
  • Athlete profile collected in sidebar
  • Chat-style interface on the main page
  • 10 coaching features selectable as glass pill buttons
  • Prompt recommendations for quick-start messaging
  • Dynamic temperature (0.3 conservative / 0.8 creative)
  • top_p tuning per category (0.85 conservative / 0.95 creative)
  • API key read from Streamlit secrets — no user-facing key input
"""

import streamlit as st
import google.generativeai as genai

# ─────────────────────────────────────────────────────────────────────────────
# Page Config  (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CoachBot AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Global CSS  ──  Dark Athletic Glassmorphism Theme
#   Fonts : Syne (display, 600–800) + DM Sans (body, 300–500)
#   Palette: #0a0d12 bg · #c6f135 electric-lime accent · frosted glass cards
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500&display=swap');

/* ── Variables ────────────────────────────────────────── */
:root {
    --bg:        #0a0d12;
    --bg2:       #0e131b;
    --surface:   rgba(255,255,255,0.04);
    --border:    rgba(255,255,255,0.08);
    --lime:      #c6f135;
    --lime-dim:  #a0c42a;
    --text:      #e8ecf0;
    --muted:     #6b788a;
    --safe-clr:  #56e39f;
    --warm-clr:  #ffb347;
    --radius:    14px;
}

/* ── Base ─────────────────────────────────────────────── */
html, body, [class*="css"], .stApp {
    background-color: var(--bg) !important;
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
    font-size: 15px;
}

/* ── Hide Streamlit chrome ────────────────────────────── */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"] { display: none !important; }

/* ── Scrollbar ────────────────────────────────────────── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(198,241,53,0.25); border-radius: 4px; }

/* ═══════════════════════════════════════════════════════
   SIDEBAR
═══════════════════════════════════════════════════════ */
[data-testid="stSidebar"] {
    background: var(--bg2) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] > div:first-child { padding: 18px 14px; }

[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stTextInput label,
[data-testid="stSidebar"] .stTextArea label,
[data-testid="stSidebar"] .stNumberInput label {
    color: var(--muted) !important;
    font-size: 11px !important;
    font-weight: 500 !important;
    letter-spacing: 0.7px;
    text-transform: uppercase;
}

[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
}
[data-testid="stSidebar"] input:focus,
[data-testid="stSidebar"] textarea:focus {
    border-color: rgba(198,241,53,0.5) !important;
    box-shadow: 0 0 0 2px rgba(198,241,53,0.12) !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] svg { fill: var(--muted); }

.sidebar-section {
    font-family: 'Syne', sans-serif;
    font-size: 11px;
    font-weight: 700;
    color: var(--lime);
    letter-spacing: 1px;
    text-transform: uppercase;
    margin: 22px 0 10px;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--border);
}

/* ═══════════════════════════════════════════════════════
   TOP BAR
═══════════════════════════════════════════════════════ */
.topbar {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 0 0 22px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 26px;
}
.topbar-logo {
    width: 42px; height: 42px;
    background: var(--lime);
    border-radius: 11px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px;
    flex-shrink: 0;
}
.topbar-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.55rem;
    font-weight: 800;
    color: #fff;
    line-height: 1;
}
.topbar-sub {
    font-size: 12px;
    color: var(--muted);
    margin-top: 3px;
}
.topbar-badge {
    margin-left: auto;
    background: rgba(198,241,53,0.1);
    border: 1px solid rgba(198,241,53,0.28);
    color: var(--lime);
    font-size: 11px;
    font-weight: 600;
    padding: 4px 13px;
    border-radius: 20px;
    letter-spacing: 0.4px;
    white-space: nowrap;
}

/* ═══════════════════════════════════════════════════════
   FEATURE BUTTONS  (glass pill morphing)
═══════════════════════════════════════════════════════ */
div.stButton > button {
    background: rgba(255,255,255,0.045);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 12.5px !important;
    font-weight: 400 !important;
    letter-spacing: 0.2px;
    padding: 8px 14px !important;
    border-radius: 50px !important;
    width: 100%;
    transition: all 0.24s cubic-bezier(0.34,1.56,0.64,1) !important;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
div.stButton > button:hover {
    background: rgba(198,241,53,0.1) !important;
    border-color: rgba(198,241,53,0.35) !important;
    color: var(--lime) !important;
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(198,241,53,0.12);
}
div.stButton > button:active {
    transform: scale(0.96) translateY(0);
}

/* Send button — larger, more prominent */
.send-btn div.stButton > button {
    background: rgba(198,241,53,0.13) !important;
    border: 1px solid rgba(198,241,53,0.4) !important;
    color: var(--lime) !important;
    font-family: 'Syne', sans-serif !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    letter-spacing: 0.6px;
    height: 56px;
    box-shadow: 0 0 20px rgba(198,241,53,0.08);
}
.send-btn div.stButton > button:hover {
    background: rgba(198,241,53,0.22) !important;
    box-shadow: 0 0 30px rgba(198,241,53,0.2) !important;
}

/* Download / clear buttons */
.stDownloadButton > button {
    background: transparent !important;
    border: 1px solid var(--border) !important;
    color: var(--muted) !important;
    font-size: 11px !important;
    border-radius: 50px !important;
    padding: 5px 14px !important;
    transition: all 0.18s !important;
}
.stDownloadButton > button:hover {
    border-color: rgba(255,255,255,0.2) !important;
    color: var(--text) !important;
}

/* ═══════════════════════════════════════════════════════
   CHAT BUBBLES
═══════════════════════════════════════════════════════ */
.msg-user {
    display: flex;
    justify-content: flex-end;
    margin: 14px 0;
}
.bubble-user {
    background: rgba(198,241,53,0.1);
    border: 1px solid rgba(198,241,53,0.22);
    color: var(--text);
    border-radius: 18px 18px 4px 18px;
    padding: 12px 18px;
    max-width: 68%;
    font-size: 14px;
    line-height: 1.65;
}

.msg-bot {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    margin: 14px 0;
}
.bot-avatar {
    width: 30px; height: 30px;
    background: var(--lime);
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 14px;
    flex-shrink: 0;
    margin-top: 4px;
}
.bubble-bot {
    background: rgba(255,255,255,0.035);
    border: 1px solid var(--border);
    backdrop-filter: blur(8px);
    color: var(--text);
    border-radius: 4px 18px 18px 18px;
    padding: 14px 20px;
    max-width: 82%;
    font-size: 14px;
    line-height: 1.75;
}

.temp-tag {
    display: inline-block;
    font-size: 10px;
    font-weight: 600;
    padding: 2px 10px;
    border-radius: 20px;
    margin-bottom: 10px;
    letter-spacing: 0.5px;
}
.temp-safe     { background: rgba(86,227,159,0.12); color: var(--safe-clr); border: 1px solid rgba(86,227,159,0.28); }
.temp-creative { background: rgba(255,179,71,0.1);  color: var(--warm-clr); border: 1px solid rgba(255,179,71,0.28); }

/* ═══════════════════════════════════════════════════════
   QUICK PROMPT CHIPS
═══════════════════════════════════════════════════════ */
.rec-wrap {
    display: flex;
    flex-wrap: wrap;
    gap: 7px;
    margin: 4px 0 16px;
}

/* ═══════════════════════════════════════════════════════
   WELCOME SCREEN
═══════════════════════════════════════════════════════ */
.welcome {
    text-align: center;
    padding: 44px 20px 36px;
    max-width: 500px;
    margin: 0 auto;
}
.welcome-icon { font-size: 48px; margin-bottom: 14px; }
.welcome h2 {
    font-family: 'Syne', sans-serif;
    font-size: 1.65rem;
    font-weight: 800;
    color: #fff;
    margin-bottom: 10px;
}
.welcome p {
    color: var(--muted);
    font-size: 13.5px;
    line-height: 1.7;
    margin-bottom: 26px;
}
.wcard-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    text-align: left;
}
.wcard {
    background: rgba(255,255,255,0.035);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px;
}
.wcard-icon { font-size: 18px; margin-bottom: 5px; }
.wcard-label { font-size: 12.5px; color: rgba(232,236,240,0.8); line-height: 1.4; }

/* ═══════════════════════════════════════════════════════
   INPUT AREA
═══════════════════════════════════════════════════════ */
.stTextArea textarea {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
    resize: none !important;
    min-height: 56px !important;
}
.stTextArea textarea:focus {
    border-color: rgba(198,241,53,0.45) !important;
    box-shadow: 0 0 0 2px rgba(198,241,53,0.1) !important;
}
.stTextArea textarea::placeholder { color: var(--muted) !important; }

/* ── Misc ─────────────────────────────────────────────── */
.divider { border: none; border-top: 1px solid var(--border); margin: 16px 0; }
.sec-label {
    font-size: 10.5px;
    font-weight: 600;
    color: var(--muted);
    letter-spacing: 0.9px;
    text-transform: uppercase;
    margin-bottom: 10px;
}
.stSpinner > div { border-top-color: var(--lime) !important; }
.stAlert { border-radius: 12px !important; font-size: 13px !important; }
[data-testid="stNumberInput"] button {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Constants & Configuration
# ─────────────────────────────────────────────────────────────────────────────

FEATURES = [
    {"key": "full_body",       "icon": "💪", "label": "Full-Body Workout",       "cat": "conservative"},
    {"key": "safe_recovery",   "icon": "🩹", "label": "Safe Recovery Plan",      "cat": "conservative"},
    {"key": "tactical_tips",   "icon": "🎯", "label": "Tactical Coaching",       "cat": "creative"},
    {"key": "nutrition_guide", "icon": "🥗", "label": "Nutrition Guide",         "cat": "creative"},
    {"key": "warmup_cooldown", "icon": "🔥", "label": "Warm-Up & Cooldown",      "cat": "conservative"},
    {"key": "mental_focus",    "icon": "🧘", "label": "Mental Focus",            "cat": "creative"},
    {"key": "hydration",       "icon": "💧", "label": "Hydration Plan",          "cat": "conservative"},
    {"key": "decision_drills", "icon": "⚡", "label": "Decision Drills",         "cat": "conservative"},
    {"key": "mobility",        "icon": "🦵", "label": "Mobility & Recovery",     "cat": "conservative"},
    {"key": "stamina",         "icon": "🏅", "label": "Tournament Stamina",      "cat": "conservative"},
]

TEMPERATURE_MAP = {"conservative": 0.3, "creative": 0.8}
TOP_P_MAP       = {"conservative": 0.85, "creative": 0.95}

PROMPT_RECS = {
    "full_body":       ["5-day workout split",     "Explosive power focus",    "Upper body strength",   "Injury prevention moves"],
    "safe_recovery":   ["Return-to-play protocol", "Low-impact week plan",     "Resistance band rehab", "Pool cardio session"],
    "tactical_tips":   ["Improve 1v1 defending",   "Pressing triggers & cues", "Attacking transitions", "Set piece routines"],
    "nutrition_guide": ["High-protein meal plan",  "Match-day eating schedule","Budget meal prep",      "Weight management"],
    "warmup_cooldown": ["Pre-match activation",    "Cold-weather warm-up",     "Dynamic mobility flow", "Post-game stretches"],
    "mental_focus":    ["Pre-match visualisation", "Overcome fear of failure", "Half-time reset ritual","Build confidence"],
    "hydration":       ["Hot-weather tournament",  "Electrolyte schedule",     "Sweat-rate tips",       "Prevent cramps"],
    "decision_drills": ["Scanning habit drills",   "3v2 overlap decisions",    "Press triggers",        "1-touch under pressure"],
    "mobility":        ["Hip flexor recovery",     "Knee-friendly flow",       "Morning joint prep",    "Foam rolling sequence"],
    "stamina":         ["8-week tournament block", "Interval running plan",    "Maintain speed 90 min", "Taper before finals"],
}

SYSTEM_PROMPT = """You are CoachBot AI — a professional youth sports coach with expertise in sports science, physiology, nutrition, and sports psychology.

Tone & Style:
• Encouraging, motivating, and safety-conscious at all times
• Address the athlete directly using "you" — make advice personal and actionable
• Use clear structure: ### headings, numbered steps, bullet points
• Include ⚠️ safety warnings wherever injury risk exists
• End every response with one short motivational sentence in bold

Format rules:
• Use ### for section headers
• Use **bold** for key terms and safety notes
• Use numbered lists for steps/exercises, bullet points for tips
• Keep language accessible for athletes aged 13–20
• ✅ = recommended  ❌ = avoid"""


# ─────────────────────────────────────────────────────────────────────────────
# Session State
# ─────────────────────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "active_feature" not in st.session_state:
    st.session_state.active_feature = "full_body"
if "pending_msg" not in st.session_state:
    st.session_state.pending_msg = ""


# ─────────────────────────────────────────────────────────────────────────────
# API Helper
# ─────────────────────────────────────────────────────────────────────────────
def get_api_key() -> str:
    try:
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        st.error(
            "⚠️ **Gemini API key not found.**\n\n"
            "Create `.streamlit/secrets.toml` and add:\n```\nGEMINI_API_KEY = \"AIza...\"\n```"
        )
        st.stop()


def call_gemini(prompt: str, temperature: float, top_p: float) -> str:
    api_key = get_api_key()
    genai.configure(api_key=api_key)
    gen_cfg = genai.types.GenerationConfig(
        temperature=temperature,
        top_p=top_p,
        max_output_tokens=2048,
    )
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=gen_cfg,
        system_instruction=SYSTEM_PROMPT,
    )
    return model.generate_content(prompt).text


# ─────────────────────────────────────────────────────────────────────────────
# Prompt Builder
# ─────────────────────────────────────────────────────────────────────────────
def build_prompt(feature_key: str, user_message: str, p: dict) -> str:
    context = (
        f"**Athlete Profile**\n"
        f"- Sport: {p['sport'] or 'Not specified'}\n"
        f"- Position: {p['position'] or 'Not specified'}\n"
        f"- Injury History / Risk Zones: {p['injuries'] or 'None reported'}\n"
        f"- Training Intensity: {p['intensity']} | Style: {p['style']}\n"
        f"- Diet: {p['diet']} | Allergies: {p['allergies'] or 'None'} | Calories: {p['calories']} kcal/day\n"
        f"- Desired Goal: {p['goal'] or 'General fitness improvement'}\n\n"
    )
    templates = {
        "full_body": (
            f"{context}Feature Request: Full-Body Workout Plan\n\n"
            f"Create a detailed 5-day full-body workout plan for a {p['position']} in {p['sport']}. "
            f"Tailor every exercise to the specific muscle demands of that position. "
            f"Intensity: {p['intensity']}. ⚠️ Avoid stressing: {p['injuries'] or 'N/A'}. "
            f"For each exercise include: name, sets × reps, rest period, and 1 coaching cue.\n\n"
            f"Athlete request: {user_message}"
        ),
        "safe_recovery": (
            f"{context}Feature Request: Safe Recovery Training Schedule\n\n"
            f"Design a 2-week recovery schedule adapting to injury: {p['injuries'] or 'general soreness'}. "
            f"Include: active recovery days, physio exercises, load management rules, "
            f"and ⚠️ red-flag signals that mean the athlete must stop immediately. "
            f"All exercises must be low-risk and age-appropriate.\n\n"
            f"Athlete request: {user_message}"
        ),
        "tactical_tips": (
            f"{context}Feature Request: Tactical Coaching Tips\n\n"
            f"Provide 10 creative, position-specific tactical tips for a {p['position']} in {p['sport']}. "
            f"For each tip: explain the concept, give a real-game scenario, and describe a drill or mental cue. "
            f"Align tips to the athlete's goal: {p['goal']}.\n\n"
            f"Athlete request: {user_message}"
        ),
        "nutrition_guide": (
            f"{context}Feature Request: 7-Day Nutrition Guide\n\n"
            f"Create a full 7-day meal plan — breakfast, mid-morning snack, lunch, pre-workout, "
            f"post-workout, dinner, evening snack each day. "
            f"Diet: {p['diet']}, Allergies: {p['allergies'] or 'none'}, ~{p['calories']} kcal/day. "
            f"Include daily macros (protein/carbs/fat) and explain how the plan supports: {p['goal']}.\n\n"
            f"Athlete request: {user_message}"
        ),
        "warmup_cooldown": (
            f"{context}Feature Request: Warm-Up & Cooldown Routine\n\n"
            f"Design a sport-specific warm-up (12–15 min) and cooldown (10 min) for a {p['position']} in {p['sport']}. "
            f"Warm-up: dynamic mobility, neural activation, CNS priming. "
            f"Cooldown: static stretching, diaphragmatic breathing. "
            f"⚠️ Avoid stress on: {p['injuries'] or 'N/A'}.\n\n"
            f"Athlete request: {user_message}"
        ),
        "mental_focus": (
            f"{context}Feature Request: Mental Focus & Pre-Match Visualisation\n\n"
            f"Build a 20-minute pre-match mental prep routine for a {p['position']} in {p['sport']}. "
            f"Include: guided visualisation script (role-specific), self-talk affirmations, "
            f"a focus keyword/anchor strategy, 4-7-8 breathing protocol, and a 5-min half-time reset.\n\n"
            f"Athlete request: {user_message}"
        ),
        "hydration": (
            f"{context}Feature Request: Hydration & Electrolyte Strategy\n\n"
            f"Develop a precise hydration plan for a {p['sport']} player at {p['intensity']} intensity. "
            f"Include: pre-training hydration (ml + timing), during-session intake (ml/hour), "
            f"electrolyte sources (sodium, potassium, magnesium), post-session rehydration, "
            f"and dehydration warning signs.\n\n"
            f"Athlete request: {user_message}"
        ),
        "decision_drills": (
            f"{context}Feature Request: Positional Decision-Making Drills\n\n"
            f"Design 8 game-speed decision drills for a {p['position']} in {p['sport']}. "
            f"For each: setup, decision cues to read, common mistakes, difficulty progression. "
            f"Safe for athlete with: {p['injuries'] or 'no current injuries'}.\n\n"
            f"Athlete request: {user_message}"
        ),
        "mobility": (
            f"{context}Feature Request: Mobility Workouts for Post-Injury Recovery\n\n"
            f"Create a 4-week progressive mobility programme targeting: {p['injuries'] or 'general flexibility'}. "
            f"Each week increases ROM safely. Include: exercise, duration/reps, technique cues, "
            f"and flag which exercises require physio approval. ⚠️ No pain-through-range movements.\n\n"
            f"Athlete request: {user_message}"
        ),
        "stamina": (
            f"{context}Feature Request: Stamina-Building for Tournament Preparation\n\n"
            f"Build an 8-week tournament readiness programme for a {p['position']} in {p['sport']}. "
            f"Phases: aerobic base → sport-specific conditioning → interval training → taper week. "
            f"Match {p['intensity']} preference. Protect: {p['injuries'] or 'N/A'}. Goal: {p['goal']}.\n\n"
            f"Athlete request: {user_message}"
        ),
    }
    return templates[feature_key]


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;padding:4px 0 18px;">
        <div style="width:34px;height:34px;background:#c6f135;border-radius:9px;
                    display:flex;align-items:center;justify-content:center;font-size:17px;">⚡</div>
        <div>
            <div style="font-family:'Syne',sans-serif;font-size:0.95rem;font-weight:800;color:#fff;">CoachBot AI</div>
            <div style="font-size:10px;color:#6b788a;">NextGen Sports Lab</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">🏟️ Sport & Position</div>', unsafe_allow_html=True)
    sport    = st.text_input("Sport", placeholder="e.g. Football, Cricket, Basketball")
    position = st.text_input("Position / Role", placeholder="e.g. Striker, Fast Bowler")

    st.markdown('<div class="sidebar-section">🩺 Health & Training</div>', unsafe_allow_html=True)
    injuries  = st.text_area("Injury History / Risk Zones",
                             placeholder="e.g. Left knee ACL (recovered), lower back tightness",
                             height=75)
    intensity = st.selectbox("Training Intensity", ["Light", "Moderate", "High", "Elite"], index=1)
    style     = st.selectbox("Training Style", [
        "Mixed / Balanced", "Strength-focused", "Endurance-focused",
        "Skills & Technique", "Speed & Agility"
    ])

    st.markdown('<div class="sidebar-section">🥗 Nutrition</div>', unsafe_allow_html=True)
    diet      = st.selectbox("Dietary Preference",
                             ["Non-Vegetarian", "Vegetarian", "Vegan", "Pescatarian"])
    allergies = st.text_input("Allergies / Intolerances", placeholder="e.g. Gluten, Nuts")
    calories  = st.number_input("Daily Calorie Target (kcal)",
                                min_value=1200, max_value=6000, value=2500, step=50)

    st.markdown('<div class="sidebar-section">🎯 Goal</div>', unsafe_allow_html=True)
    goal = st.text_area("Desired Goal",
                        placeholder="e.g. Build stamina, recover from knee injury before the season",
                        height=72)

    st.markdown("<hr style='border-color:rgba(255,255,255,0.06);margin:20px 0 12px;'>", unsafe_allow_html=True)

    # Controls row
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with c2:
        if st.session_state.messages:
            export_text = "\n\n".join(
                f"{'YOU' if m['role']=='user' else 'COACHBOT'}: {m['content']}"
                for m in st.session_state.messages
            )
            st.download_button("💾 Export", data=export_text,
                               file_name="coachbot_chat.txt",
                               mime="text/plain", use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# Athlete profile dict
# ─────────────────────────────────────────────────────────────────────────────
athlete = {
    "sport": sport, "position": position, "injuries": injuries,
    "intensity": intensity, "style": style,
    "diet": diet, "allergies": allergies, "calories": calories, "goal": goal,
}


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PAGE
# ─────────────────────────────────────────────────────────────────────────────

# Top bar
st.markdown("""
<div class="topbar">
    <div class="topbar-logo">⚡</div>
    <div>
        <div class="topbar-title">CoachBot AI</div>
        <div class="topbar-sub">Smart Fitness Assistant · Powered by Gemini 1.5 Flash</div>
    </div>
    <div class="topbar-badge">AI Coach ✦</div>
</div>
""", unsafe_allow_html=True)


# ── Feature Selection Pills ───────────────────────────────────────────────
st.markdown('<div class="sec-label">Select Coaching Feature</div>', unsafe_allow_html=True)

cols = st.columns(5)
for idx, feat in enumerate(FEATURES):
    with cols[idx % 5]:
        if st.button(
            f"{feat['icon']} {feat['label']}",
            key=f"feat_{feat['key']}",
            help=f"Temp: {TEMPERATURE_MAP[feat['cat']]} | top_p: {TOP_P_MAP[feat['cat']]} | {feat['cat'].title()}",
            use_container_width=True,
        ):
            st.session_state.active_feature = feat["key"]
            st.rerun()

# Active feature info strip
af         = next(f for f in FEATURES if f["key"] == st.session_state.active_feature)
af_temp    = TEMPERATURE_MAP[af["cat"]]
af_top_p   = TOP_P_MAP[af["cat"]]
af_color   = "#56e39f" if af["cat"] == "conservative" else "#ffb347"
af_desc    = "Conservative & Safe" if af["cat"] == "conservative" else "Creative & Expansive"
st.markdown(
    f'<div style="font-size:11px;color:{af_color};margin:8px 0 18px;">'
    f'▶ <strong style="color:{af_color}">{af["icon"]} {af["label"]}</strong>'
    f' &nbsp;·&nbsp; 🌡️ Temp {af_temp} &nbsp;·&nbsp; top_p {af_top_p}'
    f' &nbsp;·&nbsp; {af_desc}'
    f'</div>',
    unsafe_allow_html=True
)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)


# ── Chat History ──────────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("""
    <div class="welcome">
        <div class="welcome-icon">🏆</div>
        <h2>Ready to elevate your game?</h2>
        <p>Select a <strong style="color:#c6f135;">Coaching Feature</strong> above,
           pick a quick prompt or write your own question below.<br>
           Fill in your <strong style="color:#c6f135;">Athlete Profile</strong> on the left
           for fully personalised advice.</p>
        <div class="wcard-grid">
            <div class="wcard"><div class="wcard-icon">💪</div>
                <div class="wcard-label">Position-specific workouts & training plans</div></div>
            <div class="wcard"><div class="wcard-icon">🩹</div>
                <div class="wcard-label">Injury-safe recovery adapted to your history</div></div>
            <div class="wcard"><div class="wcard-icon">🥗</div>
                <div class="wcard-label">Personalised nutrition for your diet & goal</div></div>
            <div class="wcard"><div class="wcard-icon">🧘</div>
                <div class="wcard-label">Mental focus, visualisation & match-day routines</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="msg-user"><div class="bubble-user">{msg["content"]}</div></div>',
                unsafe_allow_html=True
            )
        else:
            cat = msg.get("feature_cat", "conservative")
            tag_cls   = "temp-safe" if cat == "conservative" else "temp-creative"
            tag_label = (f"🌡️ {TEMPERATURE_MAP[cat]} · Conservative"
                         if cat == "conservative"
                         else f"🌡️ {TEMPERATURE_MAP[cat]} · Creative")

            st.markdown(
                f'<div class="msg-bot">'
                f'<div class="bot-avatar">⚡</div>'
                f'<div class="bubble-bot">'
                f'<span class="temp-tag {tag_cls}">{tag_label}</span>',
                unsafe_allow_html=True
            )
            st.markdown(msg["content"])
            st.markdown("</div></div>", unsafe_allow_html=True)


# ── Prompt Recommendations ────────────────────────────────────────────────
recs = PROMPT_RECS.get(st.session_state.active_feature, [])
st.markdown('<div class="sec-label" style="margin-top:20px;">✨ Quick Prompts</div>', unsafe_allow_html=True)
rec_cols = st.columns(len(recs))
for i, rec_text in enumerate(recs):
    with rec_cols[i]:
        if st.button(rec_text, key=f"rec_{i}", use_container_width=True):
            st.session_state.pending_msg = rec_text
            st.rerun()


# ── Message Input + Send ──────────────────────────────────────────────────
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
in_col, btn_col = st.columns([5, 1])

pending = st.session_state.get("pending_msg", "")
if pending:
    st.session_state.pending_msg = ""

with in_col:
    user_input = st.text_area(
        "chat_input_label",
        value=pending,
        placeholder=f"Ask about {af['label'].lower()}… or tap a quick prompt above",
        height=56,
        label_visibility="collapsed",
        key="chat_input",
    )

with btn_col:
    st.markdown("<div class='send-btn' style='padding-top:2px;'>", unsafe_allow_html=True)
    send = st.button("Send ➤", use_container_width=True, key="send_btn")
    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Generation
# ─────────────────────────────────────────────────────────────────────────────
if send and user_input.strip():
    if not sport or not position:
        st.info(
            "💡 **Tip:** Add your sport and position in the sidebar for fully personalised advice. "
            "Generating with the context available…"
        )

    prompt = build_prompt(st.session_state.active_feature, user_input.strip(), athlete)
    st.session_state.messages.append({"role": "user", "content": user_input.strip()})

    with st.spinner("CoachBot is preparing your plan…"):
        try:
            reply = call_gemini(prompt, af_temp, af_top_p)
        except genai.types.BlockedPromptException:
            reply = (
                "⚠️ **Safety filter triggered.** Please rephrase your question "
                "and I'll be happy to help!"
            )
        except Exception as exc:
            reply = (
                f"❌ **API Error:** `{exc}`\n\n"
                "**Quick fixes:**\n"
                "- Check `GEMINI_API_KEY` in `.streamlit/secrets.toml`\n"
                "- Ensure Gemini 1.5 API is enabled in Google Cloud Console\n"
                "- Verify your network connection"
            )

    st.session_state.messages.append({
        "role": "assistant",
        "content": reply,
        "feature_cat": af["cat"],
    })
    st.rerun()

elif send and not user_input.strip():
    st.warning("Please type a message or tap a quick prompt first.")
