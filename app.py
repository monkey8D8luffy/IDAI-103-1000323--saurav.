import streamlit as st
import pandas as pd
import numpy as np
import time

# ==========================================
# Page Configuration
# ==========================================
st.set_page_config(
    page_title="AuraFit OS", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# CSS Injection: The "Glass OS" Engine
# ==========================================
def inject_custom_css(is_outdoor_mode):
    """
    Injects CSS based on the environment toggle.
    Outdoor mode = High contrast, opaque backgrounds.
    Gym mode = Translucent, blurred glass.
    """
    if is_outdoor_mode:
        # High Contrast / Matte Mode for direct sunlight
        card_bg = "rgba(20, 20, 20, 0.95)"
        border = "2px solid #FFFFFF"
        blur = "blur(0px)"
        text_shadow = "none"
    else:
        # Deep Glassmorphism Mode
        card_bg = "rgba(255, 255, 255, 0.08)"
        border = "1px solid rgba(255, 255, 255, 0.2)"
        blur = "blur(16px)"
        text_shadow = "0 2px 10px rgba(0,0,0,0.5)"

    css = f"""
    <style>
        /* Main background - simulating a deep gradient */
        .stApp {{
            background: radial-gradient(circle at top left, #1a2a6c, #111524, #111524);
        }}
        
        /* Glass Card Component */
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
        
        /* Massive Typography for sweaty/glanceable viewing */
        .glass-title {{
            font-size: 1.2rem;
            font-weight: 500;
            color: rgba(255, 255, 255, 0.7);
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 8px;
        }}
        .glass-metric {{
            font-size: 3.5rem;
            font-weight: 800;
            line-height: 1;
            margin: 0;
            background: linear-gradient(135deg, #fff 0%, #aaa 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .glass-accent-cyan {{ color: #00E5FF; text-shadow: 0 0 10px rgba(0, 229, 255, 0.4); }}
        .glass-accent-green {{ color: #00FFAA; text-shadow: 0 0 10px rgba(0, 255, 170, 0.4); }}
        .glass-accent-magenta {{ color: #FF00AA; text-shadow: 0 0 10px rgba(255, 0, 170, 0.4); }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# Helper function to render HTML cards
def glass_metric_card(title, value, unit, accent_class):
    html = f"""
    <div class="glass-card">
        <div class="glass-title">{title}</div>
        <div class="glass-metric {accent_class}">{value} <span style="font-size: 1.5rem; font-weight: normal;">{unit}</span></div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# ==========================================
# Application State & Data
# ==========================================
# Initialize session state for the environment toggle
if 'outdoor_mode' not in st.session_state:
    st.session_state.outdoor_mode = False

# ==========================================
# Main UI Layout
# ==========================================
try:
    # Top Navigation & Settings
    col_logo, col_toggle = st.columns([3, 1])
    with col_logo:
        st.markdown("<h1 style='color: white; letter-spacing: 4px;'>⚡ AURAFIT OS</h1>", unsafe_allow_html=True)
    with col_toggle:
        # Toggle to solve the visibility problem
        st.session_state.outdoor_mode = st.toggle("☀️ Outdoor Mode (High Contrast)", value=st.session_state.outdoor_mode)

    # Inject the CSS based on toggle state
    inject_custom_css(st.session_state.outdoor_mode)

    st.markdown("<br>", unsafe_allow_html=True)

    # Create Tabs for Navigation
    tab1, tab2, tab3 = st.tabs(["🏠 Dashboard", "🔥 Live Workout", "📈 Analytics"])

    # --- TAB 1: DAILY DASHBOARD ---
    with tab1:
        st.markdown("<h3 style='color: white;'>Daily Vitals</h3>", unsafe_allow_html=True)
        
        # Responsive Columns for Glass Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            glass_metric_card("Heart Rate", "68", "bpm", "glass-accent-magenta")
        with col2:
            glass_metric_card("Active Energy", "840", "kcal", "glass-accent-green")
        with col3:
            glass_metric_card("Hydration", "1.2", "L", "glass-accent-cyan")

        st.markdown("<br>", unsafe_allow_html=True)
        st.button("START TRAINING 🚀", use_container_width=True, type="primary")

    # --- TAB 2: LIVE WORKOUT (Sweaty Finger UI) ---
    with tab2:
        st.markdown("<div class='glass-card' style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h2 style='color: #00FFAA; font-size: 5rem; margin: 0;'>45:12</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: white; font-size: 1.2rem;'>ZONE 4: ANAEROBIC THRESHOLD</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Massive buttons for clumsy/sweaty interactions
        col_pause, col_stop = st.columns(2)
        with col_pause:
            st.button("PAUSE", use_container_width=True)
        with col_stop:
            st.button("END WORKOUT (Hold)", use_container_width=True, type="primary")

    # --- TAB 3: ANALYTICS ---
    with tab3:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<div class='glass-title'>Weekly Intensity Load</div>", unsafe_allow_html=True)
        
        # Generating safe, dummy data for the chart
        chart_data = pd.DataFrame(
            np.random.randint(40, 100, size=(7, 2)),
            columns=['Cardio', 'Strength'],
            index=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        )
        
        # Streamlit charts adapt reasonably well to dark themes
        st.bar_chart(chart_data, color=["#00FFAA", "#FF00AA"])
        st.markdown("</div>", unsafe_allow_html=True)

except Exception as e:
    # Robust error handling to catch rendering or data issues
    st.error("🚨 System Override: An error occurred in the AuraFit UI engine.")
    st.error(f"Error Details: {str(e)}")
    st.info("Please refresh the application.")
