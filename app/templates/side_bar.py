import streamlit as st
import os
import subprocess
import time

def render_sidebar():
    """
    Renders the navigation sidebar with environment status tracking.
    """
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Home"

    # Define navigation architecture
    menu_items = {
        "Home": "Project Overview",
        "Database": "Dataset Management",
        "LLMs" : "Model Infrastructure",
        "Persona": "Persona Profiles",
        "Pushback": "Persistence Logic",
        "Analyse": "Analyse Result"
    }

    with st.sidebar:
        st.title("Sycophancy Evaluation")
        st.caption("Analytical Framework v1.0.0")
        st.markdown("##") 
        
        # Navigation Menu
        for page_id, page_label in menu_items.items():
            if st.button(page_label, key=f"nav_{page_id}", width="stretch"):
                st.session_state.current_page = page_id
                st.rerun()

        st.markdown("---")
        st.subheader("Compute Infrastructure")
        
        # User environment identification
        try:
            cluster_user = os.getlogin()
        except Exception:
            cluster_user = os.getenv("USER", "researcher")

        # Dynamic GPU resource detection
        import torch
        has_gpu = torch.cuda.is_available()

        if not has_gpu:
            st.error("Target Node: Login Node (alex1)")
            
            # Cluster resource scanning
            existing_job_id = None
            job_state = None
            assigned_node = None
            
            try:
                check_queue = subprocess.run(
                    f"squeue -u {cluster_user} -o '%i %j %t %R'", 
                    shell=True, capture_output=True, text=True
                )
                
                for line in check_queue.stdout.split("\n"):
                    if "llm_dashboard" in line or "sycophancy" in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            existing_job_id = parts[0]
                            job_state = parts[2]
                            assigned_node = parts[3]
                            break
            except Exception:
                pass

            if existing_job_id is not None:
                st.success(f"Job Active (ID: {existing_job_id})")
                
                if job_state == "PD" or "Priority" in str(assigned_node):
                    st.warning("Status: Queued (Awaiting GPU Resources)")
                    st.info(
                        "The cluster partition is currently at capacity. "
                        "The job is registered and will be allocated a node sequentially.\n\n"
                        "Instruction: Maintain this connection. The dashboard will automatically transition "
                        "once the resource allocation is complete."
                    )
                    if st.button("Refresh Queue Status", type="secondary", width="stretch"):
                        st.rerun()
                else:
                    st.success(f"Execution Node: {assigned_node}")
                    
                    with st.expander("SSH Bridge Configuration", expanded=True):
                        st.markdown("1. Terminate local login process (Ctrl + C).")
                        st.markdown("2. Establish remote tunnel via local terminal:")
                        st.code(f"ssh -N -L 8510:{assigned_node}:8501 alex", language="bash")
                        st.caption(f"Mapped compute node: {assigned_node}")
                        st.markdown("3. Access Interface: http://localhost:8510")
                        
            else:
                st.caption("Active GPU required for evaluation tasks.")
                if st.button("Provision Compute Node (Slurm)", type="primary", width="stretch", key="btn_provision"):
                    st.info("Initializing Slurm submission...")
                    try:
                        from pathlib import Path
                        project_root = str(Path(__file__).resolve().parents[2])
                        script_path = os.path.join(project_root, "run_dashboard.sh")
                        
                        subprocess.run(
                            f"sbatch {script_path}",
                            shell=True, 
                            cwd=project_root,
                            env=os.environ.copy(),
                            capture_output=True, 
                            text=True, 
                            check=True
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"Allocation failed: {str(e)}")
                        
        else:
            node_name = os.getenv("SLURMD_NODENAME", "Compute Node")
            st.success(f"Active Node: {node_name}")
            st.caption("Compute environment verified. Evaluation matrices unlocked.")

            st.write("---")
            # Global Master Control: Flush System
            if not st.session_state.get("sidebar_flush_confirm", False):
                if st.button("Flush System Assets", type="secondary", width="stretch", key="btn_stop_sidebar"):
                    st.session_state["sidebar_flush_confirm"] = True
                    st.rerun()
            else:
                st.warning("CRITICAL ACTION")
                st.caption("This will flush model weights from VRAM, cancel requested GPU nodes, and terminate the program.")
                
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    if st.button("Confirm", type="primary", width="stretch", key="btn_stop_final"):
                        # Execute Flush Logic
                        st.session_state["pipeline_state"] = "idle"
                        st.session_state["models_loaded_in_vRAM"] = False
                        if "active_loaded_models_dict" in st.session_state:
                            st.session_state["active_loaded_models_dict"] = {}
                        
                        # Signal background process to stop if exists
                        if "stop_event" in st.session_state:
                            st.session_state.stop_event.set()
                            
                        st.session_state["sidebar_flush_confirm"] = False
                        st.session_state.current_page = "Home"
                        st.toast("System status: PURGED & TERMINATING")
                        
                        # HARD TERMINATE: Release Slurm allocation and exit process
                        job_id = os.getenv("SLURM_JOB_ID")
                        if job_id:
                            subprocess.run(f"scancel {job_id}", shell=True)
                        
                        time.sleep(1.0) # Grace period for toast
                        os._exit(0)
                with col_c2:
                    if st.button("Abort", width="stretch", key="btn_abort_sidebar"):
                        st.session_state["sidebar_flush_confirm"] = False
                        st.rerun()
