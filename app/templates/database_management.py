# app/templates/database_management.py
import streamlit as st
import time  # Explicitly imported for manual UI pacing
from app.backend.database.connect_db import (
    is_postgres_running, 
    start_postgres, 
    stop_postgres, 
    DATABASE_URL, 
    USER, 
    PROJECT_ROOT,
    engine
)
from app.backend.database.load_data import provision_essays_table, provision_json_dataset
from app.components.display_db_table import render_dynamic_table, list_all_tables

def render_database_page():
    """
    Renders the database administration and data inspection interface.
    """
    with st.container():
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 18px; margin-bottom: 10px;">
                <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#2b6cb0" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>
                <h1 style="margin: 0; padding: 0;">Dataset Management</h1>
            </div>
            """, 
            unsafe_allow_html=True
        )
        st.caption("Active PostgreSQL Cluster Management & Volume Synchronization")

    st.write(f"Active Cluster Identity: {USER}")

    server_active = is_postgres_running()

    # Environment Status Indicator
    if server_active:
        st.markdown(
            f'<div style="background-color:rgba(40, 167, 69, 0.1);padding:12px;border-radius:6px;border-left:6px solid #28a745;display:flex;align-items:center;">'
            f'<span style="height:12px;width:12px;background-color:#28a745;border-radius:50%;display:inline-block;margin-right:10px;box-shadow:0 0 8px #28a745;"></span>'
            f'<strong style="color:#28a745;">Status: PostgreSQL Engine Online</strong>'
            f'</div>', 
            unsafe_allow_html=True
        )
        st.caption(f"Network Endpoint: {DATABASE_URL}")
    else:
        st.markdown(
            f'<div style="background-color:rgba(139, 45, 45, 0.1);padding:12px;border-radius:6px;border-left:6px solid #8b2d2d;display:flex;align-items:center;">'
            f'<span style="height:12px;width:12px;background-color:#8b2d2d;border-radius:50%;display:inline-block;margin-right:10px;"></span>'
            f'<strong style="color:#ffb3b3;">Status: PostgreSQL Engine Offline</strong>'
            f'</div>', 
            unsafe_allow_html=True
        )

    st.write("---")

    # Instance Control Interface
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Initialize Database Connection", key="btn_start", disabled=server_active, type="primary", width="stretch"):
            with st.spinner("Initializing PostgreSQL cluster volumes..."):
                try:
                    start_postgres()
                    
                    # Connection synchronization loop
                    max_sync_attempts = 3
                    sync_success = False
                    
                    for attempt in range(max_sync_attempts):
                        try:
                            provision_essays_table()
                            
                            # Scan for and provision any datasets matching *_original.json or *original.json
                            import glob
                            import os
                            dataset_dir = os.path.join(PROJECT_ROOT, "data", "dataset")
                            matched_files = glob.glob(os.path.join(dataset_dir, "*_original.json"))
                            if not matched_files:
                                matched_files = glob.glob(os.path.join(dataset_dir, "*original.json"))
                                
                            if matched_files:
                                for file_path in matched_files:
                                    provision_json_dataset(os.path.basename(file_path))
                            else:
                                provision_json_dataset("full_run_llm_response_original.json")
                                
                            sync_success = True
                            break
                        except Exception as e:
                            err_msg = str(e).lower()
                            if "closed the connection" in err_msg or "operationalerror" in err_msg:
                                time.sleep(1.0)
                                continue
                            else:
                                raise e
                    
                    if sync_success:
                        st.success("Connection established. Schemas and datasets synchronized.")
                        st.rerun()
                    else:
                        st.info("System stabilization in progress. Re-initializing connection...")
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"PostgreSQL initialization failed: {e}")
                    
    with col2:
        if st.button("Terminate Database Session", key="btn_stop", disabled=not server_active, width="stretch"):
            with st.spinner("Executing graceful shutdown procedure..."):
                try:
                    stop_postgres()
                    st.warning("Database session terminated and resources released.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Shutdown signal failed: {e}")

    # Data Inspection Grid
    if server_active:
        available_tables = list_all_tables(engine)
        
        if not available_tables:
            st.warning("Null dataset detected. Verify volume provisioning.")
        else:
            default_index = 0
            if "essays" in available_tables:
                default_index = available_tables.index("essays")
            
            st.write("---")
            selected_table = st.selectbox(
                "Active Dataset Selection:",
                options=available_tables,
                index=default_index,
                help="Select the database relation for inspection."
            )
            
            render_dynamic_table(engine, selected_table)
    else:
        st.info("Instance offline. Initialize connection to access data relations.")
