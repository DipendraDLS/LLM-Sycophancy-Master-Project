import os
# SYSTEM ENVIRONMENT SANITIZATION OVERRIDE
# Prevents PyTorch 2.x from crashing due to non-standard TORCH_LOGS string values
if "TORCH_LOGS" in os.environ:
    if os.environ["TORCH_LOGS"].upper() in ["ERROR", "INFO", "WARNING", "DEBUG"]:
        del os.environ["TORCH_LOGS"]
        
        
from components.package_loader import *
from templates.llm_management import render_llm_page
from templates.database_management import render_database_page
from templates.experiment_pipeline import render_experiment_pipeline_page
from templates.persona_profiles import render_persona_profiles_page
from templates.persistence_logic import render_persistence_logic_page

# Load your custom CSS
load_css() 


# GLOBAL VRAM STATE AUTO-RECOVERY INTERCEPT
# Validates hardware memory pools to bridge global process state to user session
if hasattr(st, "_global_gpu_model_pool"):
    pool_count = len(st._global_gpu_model_pool)
    if pool_count == 3:
        # Full Integrity Recovery: All models ready
        st.session_state["models_loaded_in_vRAM"] = True
        st.session_state["active_loaded_models_dict"] = st._global_gpu_model_pool
    else:
        # State is incomplete (mid-load or empty), but we preserve what we have
        st.session_state["models_loaded_in_vRAM"] = False
else:
    st.session_state["models_loaded_in_vRAM"] = False

# GLOBAL EXPERIMENT THREAD TRACKER
if not hasattr(st, "_global_orchestrator_thread"):
    st._global_orchestrator_thread = None
if not hasattr(st, "_global_communication_queue"):
    st._global_communication_queue = None
if not hasattr(st, "_global_stop_event"):
    st._global_stop_event = None
if not hasattr(st, "_global_arena_messages"):
    st._global_arena_messages = []
if not hasattr(st, "_global_completed_nodes"):
    st._global_completed_nodes = 0


# Intercept query parameters for URL-based navigation redirection
query_params = {}
try:
    query_params = st.query_params
except AttributeError:
    try:
        query_params = st.experimental_get_query_params()
    except AttributeError:
        pass

if "page" in query_params:
    page_param = query_params["page"]
    if isinstance(page_param, list):
        page_param = page_param[0]
    
    mapping = {
        "LLMs": "LLMs",
        "Persona": "Persona",
        "Pushback": "Pushback"
    }
    if page_param in mapping:
        st.session_state.current_page = mapping[page_param]
        try:
            st.query_params.clear()
        except Exception:
            try:
                st.experimental_set_query_params()
            except Exception:
                pass

# Initialize default routing page if completely missing
if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"


# Create the Sidebar
render_sidebar()
    
    
# Inject Dynamic Active State Highlight Strip
active_id = st.session_state.current_page
st.markdown(
    f"""
    <style>
    .st-key-nav_{active_id} button {{
        background-color: rgba(255, 255, 255, 0.08) !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border-left: 4px solid #00a2ff !important; /* Professional accent highlight */
        border-radius: 0px 8px 8px 0px !important;
        filter: brightness(1.2);
    }}
    </style>
    """,
    unsafe_allow_html=True
)  
    

# Page Content Router
st.markdown("##")
if st.session_state.current_page == "Home":
    # Paste your landing page elements here...
    render_home()
    
elif st.session_state.current_page == "Database":
    render_database_page()
    
elif st.session_state.current_page == "LLMs":
    render_llm_page()
    
elif st.session_state.current_page == "Persona":
    render_persona_profiles_page()
    
elif st.session_state.current_page == "Pushback":
    render_persistence_logic_page()

elif st.session_state.current_page == "Analyse":
    from templates.analyse_results import render_analyse_page
    render_analyse_page()

elif st.session_state.current_page == "Experiment Arena":
    render_experiment_pipeline_page()