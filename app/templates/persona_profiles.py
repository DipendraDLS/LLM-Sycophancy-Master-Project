# app/templates/persona_profiles.py
import streamlit as st
from config import PERSONAS
from utils.style_loader import load_css

def parse_persona_prompt(prompt_text):
    """
    Dynamically parses the persona prompt string from config.py into structured sections.
    """
    sections = {}
    lines = prompt_text.split('\n')
    
    # Extract intro quote
    intro_lines = []
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if not line:
            index += 1
            continue
        # If it is a header, stop
        if line.endswith(':') and not line.startswith('-') and not any(char.isdigit() for char in line):
            break
        intro_lines.append(lines[index].strip())
        index += 1
        
    sections["intro_quote"] = " ".join(intro_lines)
    
    # Parse the rest
    current_key = "General"
    current_lines = []
    known_headers = [
        "Identity:", "Evaluation Dimensions (weighted equally):", "Evaluation Approach:",
        "Score Rubric:", "Score Reference:", "Scoring Behavior:", "Task:"
    ]
    
    for i in range(index, len(lines)):
        line = lines[i]
        stripped = line.strip()
        is_header = False
        for h in known_headers:
            if stripped.startswith(h) or stripped == h:
                is_header = True
                header_name = h[:-1]
                break
        
        if not is_header and stripped.endswith(':') and not stripped.startswith('-') and len(stripped) < 40 and not any(char.isdigit() for char in stripped):
            is_header = True
            header_name = stripped[:-1]
            
        if is_header:
            if current_lines:
                sections[current_key] = "\n".join(current_lines).strip()
            current_key = header_name
            current_lines = []
        else:
            current_lines.append(line)
            
    if current_lines:
        sections[current_key] = "\n".join(current_lines).strip()
        
    return sections

def render_persona_profiles_page():
    # Load stylesheet styles
    load_css()
    
    # Page Title
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 18px; margin-bottom: 10px;">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#667eea" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            <h1 style="margin: 0; padding: 0; color: #ffffff;">Persona Profiles</h1>
        </div>
        """, 
        unsafe_allow_html=True
    )
    st.write("---")
    
    # Dropdown Selector
    persona_option = st.selectbox(
        "Select Evaluator Persona:",
        options=["Neutral", "Strict", "Supportive"]
    )
    
    key = persona_option.lower()
    
    # Configurations matching the screenshots
    baselines = {
        "neutral": {
            "label": "NEUTRAL",
            "desc": "Balanced academic reviewer assessing standard dimensions without bias.",
            "val": "N/A (Uses full 1.0 - 6.0 range based purely on essay content)",
            "color": "#00a2ff",
            "glow": "rgba(0, 162, 255, 0.15)",
            "svg": """<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#00a2ff" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="display: block; margin: 0 auto 15px auto;"><line x1="12" y1="3" x2="12" y2="21" /><line x1="19" y1="21" x2="5" y2="21" /><line x1="19" y1="8" x2="5" y2="8" /><path d="M5 8l-3 7h6z" /><path d="M19 8l-3 7h6z" /></svg>"""
        },
        "strict": {
            "label": "STRICT",
            "desc": "Rigorous academic writing critic applying uncompromising quality benchmarks.",
            "val": "2.5 out of 6.0 (Historical grading reference)",
            "color": "#e53e3e",
            "glow": "rgba(229, 62, 62, 0.15)",
            "svg": """<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#e53e3e" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="display: block; margin: 0 auto 15px auto;"><path d="M20 13c0 5-3.5 7.5-7.66 9.7a1 1 0 0 1-.68 0C7.5 20.5 4 18 4 13V6a1 1 0 0 1 .76-.97l7-2a1 1 0 0 1 .48 0l7 2A1 1 0 0 1 20 6z"/></svg>"""
        },
        "supportive": {
            "label": "SUPPORTIVE",
            "desc": "Compassionate writing coach focused on student growth and motivation.",
            "val": "4.5 out of 6.0 (Historical grading reference)",
            "color": "#38a169",
            "glow": "rgba(56, 161, 105, 0.15)",
            "svg": """<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#38a169" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="display: block; margin: 0 auto 15px auto;"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 11 2 2 4-4"/></svg>"""
        }
    }
    
    cfg = baselines[key]
    raw_prompt = PERSONAS.get(key, "")
    parsed_sections = parse_persona_prompt(raw_prompt)
    
    # 2-column layout: Left (Baseline Card), Right (Persona Details)
    col_left, col_right = st.columns([1, 2])
    
    with col_left:
        baseline_card_html = f"""
        <div class="custom-card" style="border-left: 4px solid {cfg['color']}; text-align: center; padding: 30px 20px; background: linear-gradient(135deg, #1e1e2f 0%, #12121c 100%);">
            {cfg['svg']}
            <div style="font-weight: bold; letter-spacing: 1.5px; color: #ffffff; text-transform: uppercase; font-size: 1.1rem; margin-bottom: 15px;">{cfg['label']}</div>
            <div style="color: #a0aec0; font-size: 0.95rem; line-height: 1.6; margin-bottom: 30px; font-style: italic;">
                "{cfg['desc']}"
            </div>
            <hr style="border: 0; border-top: 1px solid rgba(255,255,255,0.08); margin: 20px 0;">
            <div style="text-align: left;">
                <div style="color: #718096; font-size: 0.75rem; font-weight: bold; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 8px;">Historical Baseline</div>
                <div style="color: #ffffff; font-weight: bold; font-size: 1.15rem; line-height: 1.4;">{cfg['val']}</div>
            </div>
        </div>
        """
        st.markdown(baseline_card_html, unsafe_allow_html=True)
        
    with col_right:
        # Quote system prompt
        quote = parsed_sections.get("intro_quote", "")
        if quote:
            st.markdown(f'<div style="color: #a0aec0; font-style: italic; font-size: 1.1rem; line-height: 1.5; margin-bottom: 20px;">"{quote}"</div>', unsafe_allow_html=True)
            
        # Identity Details
        identity = parsed_sections.get("Identity", "")
        if identity:
            st.markdown("### Identity Details")
            identity_bullets = [line.strip().lstrip("-* ").strip() for line in identity.split('\n') if line.strip()]
            for bullet in identity_bullets:
                st.markdown(f"- {bullet}")
                
        # Evaluation Approach / Dimensions
        approach_key = "Evaluation Approach" if "Evaluation Approach" in parsed_sections else "Evaluation Dimensions (weighted equally)"
        approach = parsed_sections.get(approach_key, "")
        if approach:
            st.markdown(f"### {approach_key}")
            approach_lines = [line.strip() for line in approach.split('\n') if line.strip()]
            for line in approach_lines:
                st.markdown(line)
                
        # Scoring Behavior
        behavior = parsed_sections.get("Scoring Behavior", "")
        if behavior:
            st.markdown("### Scoring Behavior")
            behavior_bullets = [line.strip().lstrip("-* ").strip() for line in behavior.split('\n') if line.strip()]
            for bullet in behavior_bullets:
                st.markdown(f"- {bullet}")
                
    # Score Rubric Grid
    rubric_key = "Score Rubric" if "Score Rubric" in parsed_sections else "Score Reference"
    rubric = parsed_sections.get(rubric_key, "")
    if rubric:
        st.write("---")
        st.markdown(f"## {rubric_key}")
        
        rubric_dict = {}
        lines = rubric.split('\n')
        current_score = None
        current_text = []
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if ":" in stripped and (stripped[0].isdigit() or (len(stripped) > 1 and stripped[1] == ":" and stripped[0].isdigit())):
                if current_score is not None:
                    rubric_dict[current_score] = " ".join(current_text)
                parts = stripped.split(":", 1)
                current_score = parts[0].strip()
                current_text = [parts[1].strip()]
            else:
                current_text.append(stripped)
        if current_score is not None:
            rubric_dict[current_score] = " ".join(current_text)
        
        # Row 1: 6, 5, 4
        r1_col1, r1_col2, r1_col3 = st.columns(3)
        for score, col in [('6', r1_col1), ('5', r1_col2), ('4', r1_col3)]:
            text = rubric_dict.get(score, "")
            with col:
                if text:
                    card_html = f"""
                    <div class="custom-card" style="min-height: 180px; padding: 20px; margin-bottom: 20px; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; background: linear-gradient(135deg, #1e1e2f 0%, #12121c 100%);">
                        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                            <div style="background: {cfg['color']}; color: #ffffff; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border-radius: 6px; font-weight: bold; font-size: 1.1rem;">{score}</div>
                            <span style="font-weight: 700; color: #ffffff; font-size: 1rem; letter-spacing: 0.5px; text-transform: uppercase;">Level {score}</span>
                        </div>
                        <div style="font-size: 0.95rem; color: #cbd5e0; line-height: 1.5;">{text}</div>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)
                    
        # Row 2: 3, 2, 1
        r2_col1, r2_col2, r2_col3 = st.columns(3)
        for score, col in [('3', r2_col1), ('2', r2_col2), ('1', r2_col3)]:
            text = rubric_dict.get(score, "")
            with col:
                if text:
                    card_html = f"""
                    <div class="custom-card" style="min-height: 180px; padding: 20px; margin-bottom: 20px; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; background: linear-gradient(135deg, #1e1e2f 0%, #12121c 100%);">
                        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                            <div style="background: {cfg['color']}; color: #ffffff; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border-radius: 6px; font-weight: bold; font-size: 1.1rem;">{score}</div>
                            <span style="font-weight: 700; color: #ffffff; font-size: 1rem; letter-spacing: 0.5px; text-transform: uppercase;">Level {score}</span>
                        </div>
                        <div style="font-size: 0.95rem; color: #cbd5e0; line-height: 1.5;">{text}</div>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)
                    
    # Expandable Raw Prompt
    st.write("##")
    with st.expander("🛠️ View Raw System Prompt Configuration Blueprint"):
        st.code(raw_prompt, language="text")
