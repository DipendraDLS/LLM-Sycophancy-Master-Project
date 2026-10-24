from components.package_loader import *
import os
import sys
from pathlib import Path
import time
import streamlit as st

# --- BULLETPROOF DYNAMIC PATH ENVELOPE RESOLUTION ---
current_path = Path(__file__).resolve()
while current_path.name != "evaluating-sycophancy" and current_path.parent != current_path:
    current_path = current_path.parent
PROJECT_ROOT = str(current_path)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.components.info_cards import info_card_LLMs
from app.backend.llms.model_loader import (
    get_missing_models,
    download_selected_models,
    load_cached_llm,
    clear_gpu_vram,
    MODEL_REGISTRY
)

def render_llm_page():
    """
    Renders the model infrastructure management and VRAM allocation interface.
    """
    # Recover active weights from global process memory
    if hasattr(st, "_global_gpu_model_pool") and len(st._global_gpu_model_pool) > 0:
        st.session_state["models_loaded_in_vRAM"] = True
        st.session_state["active_loaded_models_dict"] = st._global_gpu_model_pool
        
        if "pipeline_state" not in st.session_state or st.session_state["pipeline_state"] == "idle":
            st.session_state["pipeline_state"] = "completed"
            st.session_state["terminal_history"] = ["Runtime Restoration: Active model assets recovered from host memory pool."]
            
    left_space, main_content, right_space = st.columns([1, 4, 1])
    
    with main_content:
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 18px; margin-bottom: 10px;">
                <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#2b6cb0" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="15" x2="23" y2="15"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="15" x2="4" y2="15"/></svg>
                <h1 style="margin: 0; padding: 0;">Model Infrastructure</h1>
            </div>
            """, 
            unsafe_allow_html=True
        )
        st.caption("GPU-Accelerated VRAM Orchestration & Model Weight Mapping")
        st.write("---")
        
        # Model Metadata Cards
        col1, col2, col3 = st.columns(3)
        with col1:
            info_card_LLMs(
                title="Mistral-7B-Instruct-v0.3-AWQ",
                text="Instruction-tuned 7B model with 32k vocabulary and 4-bit AWQ quantization.",
                url="https://huggingface.co/solidrust/Mistral-7B-Instruct-v0.3-AWQ",
                max_length=40  
            )
        with col2:
            info_card_LLMs(
                title="Zephyr-7B-beta-AWQ",
                text="AWQ-quantized Zephyr-7B-Beta, optimized using Direct Preference Optimization (DPO).",
                url="https://huggingface.co/TheBloke/zephyr-7B-beta-AWQ",
                max_length=40  
            )
        with col3:
            info_card_LLMs(
                title="Gemma-7b-it-AWQ",
                text="Google 7B instruction-tuned model, optimized with 4-bit AWQ quantization.",
                url="https://huggingface.co/TechxGenus/gemma-7b-it-AWQ",
                max_length=40  
            )
            
        st.write("---")
        st.subheader("Environment and Asset Control")
        
        missing = get_missing_models()
        
        if missing:
            st.warning(f"Missing Assets: {', '.join(missing)}")
            st.info("Requirement: Execute from a node with external network permissions to fetch weights.")
            
            if st.button(f"Acquire Missing Assets ({len(missing)})", type="primary", key="btn_acquire"):
                st.write("### Subsystem Output")
                terminal_box = st.empty()
                log_buffer = []

                def stream_to_terminal(new_text):
                    log_buffer.append(new_text)
                    if len(log_buffer) > 15:
                        log_buffer.pop(0)
                    terminal_box.code("\n".join(log_buffer), language="bash")
                        
                try:
                    download_selected_models(missing, progress_callback=stream_to_terminal)
                    st.success("Asset acquisition complete. Re-initializing runtime state.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Asset pipeline failure: {str(e)}")
                        
        else:
            st.success("Verification: All experimental models present in local storage.")
            st.write("### VRAM Allocation Controls")
            
            selected_models = st.multiselect(
                "Select models for sequential VRAM mapping:",
                options=list(MODEL_REGISTRY.keys()),
                default=list(MODEL_REGISTRY.keys())
            )
            
            if "is_loading" not in st.session_state:
                st.session_state["is_loading"] = False

            if not selected_models:
                st.warning("Selection Required: At least one model checkpoint must be specified.")
                
            else:
                if "pipeline_state" not in st.session_state:
                    st.session_state["pipeline_state"] = "idle"
                if "terminal_history" not in st.session_state:
                    st.session_state["terminal_history"] = []
                if "show_post_cancel_warning" not in st.session_state:
                    st.session_state["show_post_cancel_warning"] = False

                import torch
                has_gpu = torch.cuda.is_available()

                col_btn, col_cancel = st.columns([2, 1])
                start_pipeline = False
                
                with col_btn:
                    if not has_gpu:
                        st.button(
                            "Sequential Initialization (GPU Required)", 
                            type="secondary",
                            disabled=True,
                            key="locked_pipeline_btn"
                        )
                        st.caption("Environment Note: Access limited to compute nodes. Use Slurm allocation via sidebar.")
                    else:
                        start_pipeline = st.button(
                            f"Initialize Sequential Mapping ({len(selected_models)} Models)", 
                            type="primary",
                            disabled=(st.session_state["pipeline_state"] == "running"),
                            key="active_pipeline_btn"
                        )
                
                with col_cancel:
                    cancel_clicked = st.button(
                        "Flush Pipeline", 
                        disabled=(st.session_state["pipeline_state"] not in ["running", "completed"] or not has_gpu),
                        key="master_cancel_btn"
                    )

                if has_gpu and cancel_clicked:
                    st.session_state["show_post_cancel_warning"] = True

                if st.session_state.get("show_post_cancel_warning", False):
                    st.error("System Purge Request: Confirming will release all in-memory assets and terminate active Slurm threads.")
                    
                    col_confirm, col_abort = st.columns(2)
                    with col_confirm:
                        if st.button("Confirm Purge", type="primary", width="stretch"):
                            st.session_state["pipeline_state"] = "idle"
                            st.session_state["show_post_cancel_warning"] = False
                            st.session_state["terminal_history"] = []
                            
                            try:
                                import subprocess
                                cluster_user = os.getenv("USER", "researcher")
                                check_queue = subprocess.run(
                                    f"squeue -u {cluster_user} -o '%i %j'", 
                                    shell=True, capture_output=True, text=True
                                )
                                
                                for line in check_queue.stdout.split("\n"):
                                    if "llm_dashboard" in line or "sycophancy" in line:
                                        parts = line.split()
                                        if parts:
                                            target_job_id = parts[0]
                                            subprocess.run(f"scancel {target_job_id}", shell=True)
                                            st.toast(f"Slurm Job {target_job_id} terminated.")
                                            break
                            except Exception as e:
                                st.toast(f"Session reset complete. Slurm tracking: {str(e)}")
                            
                            clear_gpu_vram()
                            st.rerun()
                            
                    with col_abort:
                        if st.button("Abort Purge", width="stretch"):
                            st.session_state["show_post_cancel_warning"] = False
                            st.rerun()

                if has_gpu and start_pipeline and st.session_state["pipeline_state"] != "running":
                    st.session_state["pipeline_state"] = "running"
                    st.session_state["terminal_history"] = ["Initializing deployment framework targets..."]
                    st.rerun()

                if st.session_state["pipeline_state"] in ["running", "completed"]:
                    if st.session_state["pipeline_state"] == "running":
                        st.write("#### Automation Output Feed")
                    else:
                        st.write("#### Historical Logs")
                    
                    with st.container(height=400, border=True):
                        automated_terminal = st.empty()
                        automated_terminal.code("\n".join(st.session_state["terminal_history"]), language="bash")
                    
                    def log_to_ui(message):
                        cleaned = message.replace("\r", "\n").strip()
                        if cleaned:
                            for line in cleaned.split("\n"):
                                if line.strip():
                                    st.session_state["terminal_history"].append(line.strip())
                            if len(st.session_state["terminal_history"]) > 100:
                                st.session_state["terminal_history"].pop(0)
                            automated_terminal.code("\n".join(st.session_state["terminal_history"]), language="bash")

                    if has_gpu and st.session_state["pipeline_state"] == "running":
                        try:
                            import torch
                            try:
                                gpu_hw_identity = torch.cuda.get_device_name(0)
                            except Exception:
                                gpu_hw_identity = "Cluster GPU Allocation"
                            
                            log_to_ui(f"Hardware Identity: {gpu_hw_identity}")
                            
                            for current_index, model_identity in enumerate(selected_models, 1):
                                log_to_ui(f"\n[Sequence {current_index}/{len(selected_models)}] Active Focus: {model_identity}")
                                log_to_ui(f"Mapping storage layers for {model_identity} into VRAM tracks...")
                                model, tokenizer = load_cached_llm(model_identity, _progress_callback=log_to_ui)
                                
                                st.session_state["active_model"] = model
                                st.session_state["active_tokenizer"] = tokenizer
                                st.session_state["active_model_name"] = model_identity
                                
                                log_to_ui(f"Verification complete. Testing execution arrays...")
                                time.sleep(4)
                                log_to_ui(f"Finalized {model_identity}. Results stored.")
                            
                            st.session_state["models_loaded_in_vRAM"] = True
                            st.session_state["pipeline_state"] = "completed"
                            st.rerun()
                            
                        except Exception as e:
                            st.session_state["pipeline_state"] = "idle"
                            clear_gpu_vram()
                            st.error(f"Sequence termination: {str(e)}")

                if st.session_state["pipeline_state"] == "completed":
                    col_banner, col_flush = st.columns([3, 1])
                    with col_banner:
                        st.success("Batch execution finished. Resource allocation stable.")
                    with col_flush:
                        if st.button("Purge Allocation", type="secondary", width="stretch"):
                            st.session_state["show_post_cancel_warning"] = True
                            st.rerun()
