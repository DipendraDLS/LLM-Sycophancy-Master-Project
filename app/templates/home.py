
from components.package_loader import *

from backend.database.connect_db import is_postgres_running
from backend.orchestration.gpu_validator import is_gpu_node_available

def render_home():
    """
    Renders the central project overview and system status.
    """
    left_space, main_content, right_space = st.columns([1, 4, 1])

    with main_content:
        st.markdown(
            """
            <div style="display: flex; align-items: flex-start; gap: 20px; margin-bottom: 20px;">
                <div style="margin-top: 10px;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="52" height="52" viewBox="0 0 24 24" fill="none" stroke="#38a169" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                    </svg>
                </div>
                <div>
                    <h2 style="margin: 0; padding: 0; line-height: 1.2;">Sycophancy Vs Truth: Testing how LLMs Change their mind to please the user. </h2>
                    <p style="margin: 5px 0 0 0; opacity: 0.7; font-size: 1.1rem;">Evaluation of Model Drift</p>
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        st.write("---")
        
        col1, col2, col3 = st.columns(3)

        with col1:
            info_card(
                '<a href="?page=LLMs" target="_self" class="card-title-link">Model Pool</a>',
                "Mistral-7B, Zephyr-7B, Gemma-7B"
            )

        with col2:
            info_card(
                '<a href="?page=Persona" target="_self" class="card-title-link">Persona Profiles</a>',
                "Neutral, Strict, Supportive"
            )

        with col3:
            info_card(
                '<a href="?page=Pushback" target="_self" class="card-title-link">Pushback Strategies</a>',
                "Direct, Authoritative, Empathetic"
            )
            
        st.write("### Project Objectives")
        
        # --- BESPOKE OBJECTIVES GRID ---
        col_obj1, col_obj2 = st.columns(2)
        
        with col_obj1:
            st.markdown(
                """
                <div style="background: rgba(255,255,255,0.03); border-left: 4px solid #38a169; padding: 20px; border-radius: 0 10px 10px 0; margin-bottom: 20px; min-height: 180px;">
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 10px;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#38a169" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 3h5v5"/><path d="M8 3H3v5"/><path d="m21 3-7.5 7.5"/><path d="m3 3 7.5 7.5"/><line x1="12" x2="12" y1="13" y2="21"/></svg>
                        <strong style="font-size: 1.1rem; color: #f0f7ff;">Compare Alignment Paradigms</strong>
                    </div>
                    <p style="font-size: 0.9rem; opacity: 0.8; margin: 0;">Evaluation of <code style="color: #68d391;">SFT</code>, <code style="color: #68d391;">RLHF</code>, and <code style="color: #68d391;">DPO</code> aligned architectures to determine drift variance.</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            st.markdown(
                """
                <div style="background: rgba(255,255,255,0.03); border-left: 4px solid #ecc94b; padding: 20px; border-radius: 0 10px 10px 0; margin-bottom: 20px; min-height: 180px;">
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 10px;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#ecc94b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="m16 10-4 4-4-4"/></svg>
                        <strong style="font-size: 1.1rem; color: #f0f7ff;">Quantify Susceptibility</strong>
                    </div>
                    <p style="font-size: 0.9rem; opacity: 0.8; margin: 0;">Metric-based assessment of baseline interactive biases and persona-induced confirmation drift.</p>
                </div>
                """, 
                unsafe_allow_html=True
            )

        with col_obj2:
            st.markdown(
                """
                <div style="background: rgba(255,255,255,0.03); border-left: 4px solid #4299e1; padding: 20px; border-radius: 0 10px 10px 0; margin-bottom: 20px; min-height: 180px;">
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 10px;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#4299e1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m19 11-4-7"/><path d="m19 11-4 7"/><path d="M19 11H5"/><path d="m5 11 4 7"/><path d="m5 11 4-7"/></svg>
                        <strong style="font-size: 1.1rem; color: #f0f7ff;">Analyze Score Drift</strong>
                    </div>
                    <p style="font-size: 0.9rem; opacity: 0.8; margin: 0;">Observation of cumulative response decay and logic compromise over extended discourse phases.</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            st.markdown(
                """
                <div style="background: rgba(255,255,255,0.03); border-left: 4px solid #f56565; padding: 20px; border-radius: 0 10px 10px 0; margin-bottom: 20px; min-height: 180px;">
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 10px;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f56565" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="M19 9l-5 5-4-4-3 3"/></svg>
                        <strong style="font-size: 1.1rem; color: #f0f7ff;">Map Behavioral Trajectories</strong>
                    </div>
                    <p style="font-size: 0.9rem; opacity: 0.8; margin: 0;">Visualization of decision-making shifts and reasoning pivots within high-pressure adversarial contexts.</p>
                </div>
                """, 
                unsafe_allow_html=True
            )

        st.write("##") 
        
        # System Validation
        db_ok = is_postgres_running()
        gpu_ok = is_gpu_node_available()
        
        # Development status overrides (to be toggled in production)
        # db_ok = True
        # gpu_ok = True
        
        models_loaded = st.session_state.get("models_loaded_in_vRAM", False)
        pipeline_running = st.session_state.get("pipeline_running", False)
        ready_to_launch = db_ok and gpu_ok and models_loaded
        
        # Determine button state based on active pipeline
        if pipeline_running:
            # Shift to Resume mode if already active
            if st.button("Resume Active Evaluation Arena", key="main_launch_trigger", type="primary", width="stretch"):
                st.session_state.current_page = "Experiment Arena"
                st.rerun()
            st.info("System Status: Background evaluation orchestration is currently in progress.")
        else:
            # Default initialization mode
            if st.button("Initialize Evaluation Environment", key="main_launch_trigger", type="primary", width="stretch", disabled=not ready_to_launch):
                st.session_state.current_page = "Experiment Arena"
                st.rerun()

        if not ready_to_launch:
            st.markdown("<br>", unsafe_allow_html=True)
            guide_box = '<div style="background-color: rgba(255, 193, 7, 0.1); padding: 15px; border-radius: 8px; border: 1px solid #ffc107;">'
            guide_box += '<strong style="color: #ffc107;">System Prerequisites Status:</strong><ul style="margin-top: 5px; margin-bottom: 0px; font-size: 13px; color:#cccccc;">'
            
            if not gpu_ok:
                guide_box += '<li><b>GPU Resources Unallocated:</b> Active CUDA node binding required for model inference.</li>'
            if not db_ok:
                guide_box += '<li><b>Database Instance Offline:</b> Local PostgreSQL backend connectivity required.</li>'
            if not models_loaded:
                guide_box += '<li><b>Model Weights Incomplete:</b> All 3 models must be mapped into VRAM. Finish the sequence in <b>Model Infrastructure</b> or use <b>Flush</b> to reset.</li>'
                
            guide_box += '</ul></div>'
            st.markdown(guide_box, unsafe_allow_html=True)