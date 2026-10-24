# app/templates/persistence_logic.py
import streamlit as st
import pandas as pd
from config import PUSHBACKS
from utils.style_loader import load_css

def render_persistence_logic_page():
    # Load stylesheet styling
    load_css()
    
    # Page Header
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 18px; margin-bottom: 10px;">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#ed64a6" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="1 4 1 10 7 10"/><polyline points="23 20 23 14 17 14"/><path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"/></svg>
            <h1 style="margin: 0; padding: 0; color: #ffffff;">Persistence Logic</h1>
        </div>
        """, 
        unsafe_allow_html=True
    )
    st.markdown("Explore the multi-turn conversational pushback messages used during experiments to measure model stance persistence.")
    st.write("---")
    
    # Selector controls
    col_strat, col_dir = st.columns([1, 1])
    
    with col_strat:
        strategy = st.selectbox(
            "Pushback Strategy Mode",
            options=["direct", "authority_based", "empathy_based"],
            format_func=lambda s: s.replace("_", " ").title() + " Pushback"
        )
        
    with col_dir:
        direction = st.selectbox(
            "Drift Target Direction",
            options=["positive", "negative"],
            format_func=lambda d: "Positive Drift (Pushing for Higher Score)" if d == "positive" else "Negative Drift (Pushing for Lower Score)"
        )
        
    # Conversation simulation flow
    st.write("### Interactive Turn Escalation Simulator")
    
    strategy_data = PUSHBACKS.get(strategy, {})
    direction_data = strategy_data.get(direction, {})
    
    if direction_data:
        turns = ["turn1", "turn2", "turn3"]
        colors = {
            "turn1": {"bg": "rgba(49, 130, 206, 0.1)", "border": "#3182ce", "label": "Initial Disagreement (Turn 1)"},
            "turn2": {"bg": "rgba(221, 107, 32, 0.1)", "border": "#dd6b20", "label": "Assertive Pushback (Turn 2)"},
            "turn3": {"bg": "rgba(229, 62, 62, 0.1)", "border": "#e53e3e", "label": "Extreme Escalation (Turn 3)"}
        }
        
        for turn in turns:
            text = direction_data.get(turn, "")
            t_config = colors[turn]
            
            chat_html = f"""
            <div style="background: {t_config['bg']}; border-left: 5px solid {t_config['border']}; border-radius: 6px; padding: 16px 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.15);">
                <strong style="color: {t_config['border']}; font-size: 0.95rem; text-transform: uppercase; letter-spacing: 1px;">{t_config['label']}</strong>
                <p style="margin: 8px 0 0 0; font-size: 1.05rem; line-height: 1.5; color: #e2e8f0; font-style: italic;">&ldquo;{text}&rdquo;</p>
            </div>
            """
            st.markdown(chat_html, unsafe_allow_html=True)
            
    # Comparative Reference Table
    st.write("##")
    st.write("### Global Strategy Comparison Reference")
    
    rows = []
    for strat_key, strat_val in PUSHBACKS.items():
        for dir_key, dir_val in strat_val.items():
            rows.append({
                "Strategy": strat_key.replace("_", " ").title(),
                "Direction": "Positive (Higher)" if dir_key == "positive" else "Negative (Lower)",
                "Turn 1": dir_val.get("turn1", ""),
                "Turn 2": dir_val.get("turn2", ""),
                "Turn 3": dir_val.get("turn3", "")
            })
            
    df = pd.DataFrame(rows)
    st.dataframe(df, width='stretch')
