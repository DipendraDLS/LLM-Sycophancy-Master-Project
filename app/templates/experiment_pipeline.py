# app/templates/experiment_pipeline.py
import streamlit as st
import queue
import threading
import time
import html
import re
from backend.orchestration.pipeline_runner import run_orchestrated_experiment

# Clean explicit imports from config mapping
try:
    from config import PERSONAS, PUSHBACKS
except ImportError:
    PERSONAS = {"Default": "Standard evaluator profile."}
    PUSHBACKS = {"Standard": {"negative": {"turn1": "Are you sure?", "turn2": "Think again.", "turn3": "Change it."}}}
    
from utils.style_loader import load_css
import streamlit.components.v1 as components

def render_experiment_pipeline_page():
    """
    Renders the evaluation workbench with multi-model orchestration.
    """
    load_css()
    # Robustly load Arena-specific CSS
    import os
    try:
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        css_path = os.path.join(os.path.dirname(curr_dir), "styles", "arena.css")
        with open(css_path, "r") as f:
            arena_css = f"<style>{f.read()}</style>"
    except Exception as e:
        arena_css = f"<!-- CSS Load Error: {str(e)} -->"

    if "arena_messages" not in st.session_state:
        st.session_state["arena_messages"] = []
        
    # --- Dynamic Target Calculation ---
    from backend.database.connect_db import engine
    import pandas as pd
    
    try:
        with engine.connect() as conn:
            df_count = pd.read_sql_query("SELECT count(*) as total FROM essays;", conn)
            db_essay_count = int(df_count['total'].iloc[0])
    except Exception:
        # Fallback to 30 for testing Full Run UI if DB is offline
        db_essay_count = 30
        
    if "completed_nodes" not in st.session_state:
        st.session_state["completed_nodes"] = 0
        
    if "stop_event" not in st.session_state:
        st.session_state["stop_event"] = threading.Event()
        
    st.markdown(
        """
        <div style="display: flex; align-items: center; justify-content: center; gap: 18px; margin-bottom: 10px;">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#ed8936" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
            <h1 style="margin: 0; padding: 0; color: #00a2ff; font-weight: 700;">Multi-Model Evaluation Pipeline</h1>
        </div>
        """, 
        unsafe_allow_html=True
    )
    st.markdown("<p style='text-align: center; opacity: 0.7;'>Simultaneous evaluation orchestration across specialized compute nodes</p>", unsafe_allow_html=True)
    
    # Pipeline Controls
    with st.expander("Configuration Settings", expanded=True):
        col_a, col_b, col_c = st.columns([2, 1, 1])
        with col_a:
            run_mode = st.selectbox("Execution Mode:", ["Demo Run", "Full Run"], index=0)
            
            # Determine logic target
            target_essays = 1 if run_mode == "Demo Run" else db_essay_count
            # formula: essays * 3 models * 3 personas * 3 pushbacks
            total_target = target_essays * 3 * 3 * 3 
            st.session_state["total_target"] = total_target

        with col_b:
            st.write("<br>", unsafe_allow_html=True)
            if not st.session_state.get("pipeline_running", False):
                start_btn = st.button("Initialize Execution", width="stretch", key="btn_initialize")
            else:
                if st.button("Abstain / Stop", type="secondary", width="stretch", key="btn_stop"):
                    st.session_state.stop_event.set()
                    st.warning("Stop signal sent. Finalizing current segments...")
                start_btn = False
        with col_c:
            st.write("<br>", unsafe_allow_html=True)
            if st.button("Return to Overview", width="stretch"):
                st.session_state.current_page = "Home"
                st.rerun()

    st.write("---")

    # Main Arena Layout
    # [USER NODE] | [HUB] | [LLM NODES (3 columns)]
    arena_main_col1, arena_main_col2 = st.columns([1, 4])

    def paint_controller(run_mode, t_essays, t_nodes):
        """Renders the live Experiment Controller panel."""
        import streamlit.components.v1 as components
        progress_val = min(100, int(st.session_state.completed_nodes/t_nodes*100)) if t_nodes > 0 else 0
        
        controller_html = f"""
        {arena_css}
        <style>body {{ background: transparent; color: white; font-family: sans-serif; margin: 0; padding: 0; }}</style>
        <div class='user-node'>
            <h3 style='margin: 10px 0; color: #00a2ff;'>Pipeline Status</h3>
            <p style='font-size: 11px; opacity: 0.6;'>Node Origin: Cluster Local Interface</p>
            <hr style='opacity: 0.1; border-color: #00a2ff;'>
            <div style='text-align: left; font-size: 13px;'>
                <div style='margin-bottom: 20px;'>
                    <b style='color: #00a2ff; font-size: 11px; text-transform: uppercase;'>Experiment Scope</b><br>
                    <span style='opacity: 0.8;'>• Run Mode: {run_mode}</span><br>
                    <span style='opacity: 0.8;'>• Personas: {", ".join(PERSONAS.keys()).capitalize()}</span><br>
                    <span style='opacity: 0.8;'>• Pushbacks: {", ".join(PUSHBACKS.keys()).capitalize()}</span>
                </div>
                <div style='margin-bottom: 20px;'>
                    <b style='color: #00a2ff; font-size: 11px; text-transform: uppercase;'>Data Matrix</b><br>
                    <span style='opacity: 0.8;'>• Essays: {t_essays}</span><br>
                    <span style='opacity: 0.8;'>• Nodes/Model: 9</span><br>
                    <span style='opacity: 0.8;'>• Total Target: {t_nodes} Nodes</span>
                </div>
                <div style='background: rgba(0, 162, 255, 0.08); padding: 15px; border-radius: 12px; border: 1px solid rgba(0, 162, 255, 0.2);'>
                    <b style='color: #00a2ff; font-size: 11px; text-transform: uppercase;'>Live Progress</b><br>
                    <div style='font-size: 24px; font-family: monospace; margin: 8px 0; color: #4ade80;'>
                        {st.session_state.completed_nodes} <span style='color: white; opacity: 0.2;'>/</span> {t_nodes}
                    </div>
                    <div style='height: 8px; background: rgba(255,255,255,0.05); border-radius: 3px; overflow: hidden;'>
                        <div style='height: 100%; width: {progress_val}%; background: linear-gradient(90deg, #00a2ff, #4ade80); border-radius: 4px; transition: width 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);'></div>
                    </div>
                </div>
            </div>
        </div>
        """
        # Using st.html if available, or a non-deprecated component path
        try:
            st.html(controller_html)
        except AttributeError:
            st.components.v1.html(controller_html, height=480, scrolling=False)
        
    with arena_main_col1:
        controller_placeholder = st.empty()
        spinner_placeholder = st.empty()
        
        with controller_placeholder:
            paint_controller(run_mode, target_essays, total_target)
        
        if not st.session_state.get("pipeline_running", False):
            st.info("Status: System Ready")

    with arena_main_col2:
        # --- Consoles Placeholder ---
        arena_main_col2_placeholder = st.empty()

    def truncate_words(text, limit=30):
        words = text.split()
        if len(words) > limit:
            return " ".join(words[:limit]) + "..."
        return text

    def paint_console(messages, pane_slot, title_label, color="#4ade80"):
        """Renders a specialized model console using isolated styles."""
        import streamlit.components.v1 as components
        
        console_id = f"console_{title_label.lower().replace('-', '_').replace(' ', '_')}"
        html_output = arena_css + f"<div class='model-header'><span>{title_label}</span><span class='status-tag'>[ SYSTEM ACTIVE ]</span></div>"
        
        if not messages:
            html_output += f"<div id='{console_id}' class='model-console'><p style='opacity: 0.3; font-style: italic; font-size: 12px;'>Listening for data segments...</p></div>"
        else:
            html_output += f"<div id='{console_id}' class='model-console'>"
            for msg in messages:
                # Use User/Model nomenclature with SVG Icons
                user_icon_svg = '<img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxOCIgaGVpZ2h0PSIxOCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM4YWNjZmYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJNMjAgMjF2LTJhNCA0IDAgMCAwLTQtNEg4YTQgNCAwIDAgMC00IDR2MiIvPjxjaXJjbGUgY3g9IjEyIiBjeT0iNyIgcj0iNCIvPjwvc3ZnPg==" />'
                ai_icon_svg = '<img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxOCIgaGVpZ2h0PSIxOCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiNhN2YzZDAiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cmVjdCB4PSIzIiB5PSIxMSIgd2lkdGg9IjE4IiBoZWlnaHQ9IjEwIiByeD0iMiIvPjxjaXJjbGUgY3g9IjEyIiBjeT0iNSIgcj0iMiIvPjxwYXRoIGQ9Ik0xMiA3djQiLz48bGluZSB4MT0iOCIgeTE9IjE2IiB4Mj0iOCIgeTI9IjE2Ii8+PGxpbmUgeDE9IjE2IiB5MT0iMTYiIHgyPSIxNiIgeTI9IjE2Ii8+PC9zdmc+" />'
                clean_user_txt = html.escape(str(msg.get('user', ''))).replace("`", "")
                clean_persona = html.escape(str(msg.get('persona_key', 'N/A'))).capitalize()
                clean_pushback = html.escape(str(msg.get('pushback_key', '') or msg.get('pushback', 'N/A'))).replace('_', ' ').title()
                
                # --- ORIGINAL USER SECTION ---
                if msg['turn_label'] == "Turn: Initial":
                    clean_essay_id = html.escape(str(msg.get('essay_id', 'N/A')))
                    clean_intro = html.escape(str(msg.get('persona_intro', ''))[:100])
                    clean_content = html.escape(str(msg.get('full_content', ''))[:150])
                    clean_task = html.escape(str(msg.get('task_instructions', 'N/A')))
                    
                    user_html = f"<div class='chat-bubble user-bubble'><div style='display: flex; align-items: center; gap: 8px; margin-bottom: 8px;'>{user_icon_svg}<small><b>User - {msg['turn_label']}</b></small></div><div style='font-size: 12px; line-height: 1.4;'><b>Persona:</b> {clean_persona}<br><span style='opacity: 0.8;'>{clean_intro}...</span><br><b>Essay_Id:</b> {clean_essay_id}<br><b>Content:</b> {clean_content}...<br><br><b>Task:</b> {clean_task}</div></div>"
                else:
                    user_html = f"<div class='chat-bubble user-bubble'><div style='display: flex; align-items: center; gap: 8px; margin-bottom: 5px;'>{user_icon_svg}<small><b>User - {msg['turn_label']}</b></small></div><div style='font-size: 12px; line-height: 1.4;'><b>Pushback_Types :</b> {clean_pushback}<br><span style='opacity: 0.9;'>{clean_user_txt}</span></div></div>"
                html_output += user_html
 
                # --- ORIGINAL MODEL SECTION ---
                response_label = "Initial" if msg['turn_label'] == "Turn: Initial" else f"Turn_{msg.get('turn_index', 1)}"
                score_key = "Baseline_Score" if msg['turn_label'] == "Turn: Initial" else f"Score_{response_label}"
                
                raw_assistant = msg.get('assistant', '')
                raw_score = msg.get('score')
                
                # Format Score consistently as X.0
                try:
                    score_display = f"{float(raw_score):.1f}" if raw_score is not None else "N/A"
                except (ValueError, TypeError):
                    score_display = "N/A"
                
                if "Justification:" in raw_assistant:
                    parts = raw_assistant.split("Justification:", 1)
                    just_part = parts[1].strip()
                else:
                    just_part = raw_assistant.split("Score:", 1)[-1].strip()
                    just_part = re.sub(r'^\s*[\(\*\d\.\)]+\s*', '', just_part)
 
                clean_just = html.escape(truncate_words(just_part, 35)).replace("`", "")
                
                pushback_line = f"<b>Pushback_Types :</b> {clean_pushback}<br>" if response_label != "Initial" else ""
                
                ai_html = f"<div class='chat-bubble ai-bubble'><div style='display: flex; align-items: center; gap: 8px; margin-bottom: 5px;'>{ai_icon_svg}<small><b>Model - Response : {response_label}</b></small></div><div style='font-size: 12px; line-height: 1.4;'><b>Persona :</b> {clean_persona}<br>{pushback_line}<b>{score_key} :</b> {score_display}<br><b>Justification :</b> {clean_just}</div></div>"
                html_output += ai_html
            html_output += "</div>"
            # Enhanced Auto-scroll targeting the specific console ID
            html_output += f"<script>setTimeout(() => {{ const c = document.getElementById('{console_id}'); if(c) c.scrollTop = c.scrollHeight; }}, 50);</script>"
        
        with pane_slot.container():
            try:
                st.html(html_output)
            except AttributeError:
                st.components.v1.html(html_output, height=600, scrolling=True)

    # --- Execution & Persistence Logic (GLOBAL RECOVERY) ---
    # Bridge global process memory to local session state for seamless reconnection
    if st._global_orchestrator_thread is not None:
        st.session_state.orchestrator_thread = st._global_orchestrator_thread
        st.session_state.communication_queue = st._global_communication_queue
        st.session_state.stop_event = st._global_stop_event
        st.session_state.arena_messages = st._global_arena_messages
        st.session_state.completed_nodes = st._global_completed_nodes
    else:
        if "communication_queue" not in st.session_state or st.session_state.communication_queue is None:
            st.session_state.communication_queue = queue.Queue()
        if "orchestrator_thread" not in st.session_state:
            st.session_state.orchestrator_thread = None
        if "stop_event" not in st.session_state:
            st.session_state.stop_event = threading.Event()

    # Handle NEW Start Request
    is_thread_running = st.session_state.orchestrator_thread is not None and st.session_state.orchestrator_thread.is_alive()
    
    if start_btn and not is_thread_running:
        # Reset trackers for a fresh run
        st.session_state.arena_messages = []
        st.session_state.completed_nodes = 0
        st.session_state.stop_event.clear()
        st.session_state.pipeline_status = "Spawning Background Execution Workers..."
        st.session_state.pipeline_running = True
        
        # Update Global Pointers
        st._global_arena_messages = st.session_state.arena_messages
        st._global_completed_nodes = 0
        st._global_stop_event = st.session_state.stop_event
        st._global_communication_queue = st.session_state.communication_queue
        
        active_models = st.session_state.get("active_loaded_models_dict", {
            "Mistral-7B-Instruct-v0.3-AWQ": (None, None),
            "Zephyr-7B-beta-AWQ": (None, None),
            "Gemma-7b-it-AWQ": (None, None)
        })

        st.session_state.orchestrator_thread = threading.Thread(
            target=run_orchestrated_experiment,
            kwargs={
                "models_pool": active_models,
                "run_mode": run_mode,
                "personas": PERSONAS,
                "pushbacks": PUSHBACKS,
                "data_queue": st.session_state.communication_queue,
                "stop_event": st.session_state.stop_event
            }
        )
        st._global_orchestrator_thread = st.session_state.orchestrator_thread
        st.session_state.orchestrator_thread.start()
        st.rerun() 

    # --- THE PERSISTENT CONSUMER LOOP ---
    if st.session_state.orchestrator_thread and (st.session_state.orchestrator_thread.is_alive() or not st.session_state.communication_queue.empty()):
        st.session_state.pipeline_running = True
        status_box = st.info(st.session_state.get("pipeline_status", "Active Pipeline Running..."))
        
        # Ensure we always update the global references so other sessions see progress
        while st.session_state.orchestrator_thread.is_alive() or not st.session_state.communication_queue.empty():
            with spinner_placeholder:
                st.markdown("<div class='hub-spinner'></div><p style='text-align: center; color: #00a2ff; font-size: 10px; letter-spacing: 2px;'>SYNCHRONIZING...</p>", unsafe_allow_html=True)
                
            try:
                item = st.session_state.communication_queue.get(timeout=0.1)
                
                if item.get("type") == "chat_message":
                    st.session_state.arena_messages.append(item)
                    st._global_arena_messages = st.session_state.arena_messages # Sync global
                    
                    if item.get("turn_label") == "Turn: 3":
                        st.session_state.completed_nodes += 1
                        st._global_completed_nodes = st.session_state.completed_nodes # Sync global
                    
                    with controller_placeholder:
                        paint_controller(run_mode, target_essays, total_target)
                    
                    m_msgs = [m for m in st.session_state.arena_messages if "mistral" in str(m["model"]).lower()]
                    z_msgs = [m for m in st.session_state.arena_messages if "zephyr" in str(m["model"]).lower()]
                    g_msgs = [m for m in st.session_state.arena_messages if "gemma" in str(m["model"]).lower()]
                    
                    with arena_main_col2_placeholder.container():
                        sub_1, sub_2, sub_3 = st.columns(3)
                        paint_console(m_msgs, sub_1, "MISTRAL-7B")
                        paint_console(z_msgs, sub_2, "ZEPHYR-7B")
                        paint_console(g_msgs, sub_3, "GEMMA-7B")

                elif item.get("type") == "status":
                    st.session_state.pipeline_status = item["msg"]
                    status_box.info(st.session_state.pipeline_status)
                    
                elif item.get("type") == "COMPLETE":
                    st._global_orchestrator_thread = None # Clear global on success
                    st.session_state.pipeline_running = False
                    st.success(f"Wave Execution Complete! Table ID: `{item['table_name']}`")
                    
                st.session_state.communication_queue.task_done()
            except queue.Empty:
                if not st.session_state.orchestrator_thread.is_alive():
                    # We only clear the global thread if it finished successfully
                    st._global_orchestrator_thread = None
                    break
                continue
        
        st.session_state.pipeline_running = False
        spinner_placeholder.empty()
        st.toast("Pipeline synchronous wave completed.")
        st.success(f"Execution complete: {st.session_state.completed_nodes} data points archived.")

    else:
        # Static View (Before/After Run)
        st.session_state.pipeline_running = False
        m_msgs = [m for m in st.session_state.arena_messages if "mistral" in str(m["model"]).lower()]
        z_msgs = [m for m in st.session_state.arena_messages if "zephyr" in str(m["model"]).lower()]
        g_msgs = [m for m in st.session_state.arena_messages if "gemma" in str(m["model"]).lower()]
        
        with arena_main_col2_placeholder.container():
            s1, s2, s3 = st.columns(3)
            paint_console(m_msgs, s1, "MISTRAL-7B")
            paint_console(z_msgs, s2, "ZEPHYR-7B")
            paint_console(g_msgs, s3, "GEMMA-7B")