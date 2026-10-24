# app/components/display_db_table.py
import streamlit as st
import pandas as pd
from sqlalchemy import text

def list_all_tables(engine):
    """Fetches a list of all user-defined table names in the public schema."""
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            result = conn.execute(query)
            return [row[0] for row in result]
    except Exception as e:
        st.error(f"Error fetching table list: {e}")
        return []

def get_total_row_count(engine, table_name, search_term=""):
    """Counts the total number of records in a specific table, potentially filtered by search."""
    try:
        with engine.connect() as conn:
            if not search_term:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name};"))
            else:
                # SMART SEARCH: Search across all columns by converting row to text
                # Note: This is a Postgres-specific trick for global table search
                query = text(f"SELECT COUNT(*) FROM {table_name} WHERE ROW({table_name})::text ILIKE :search;")
                result = conn.execute(query, {"search": f"%{search_term}%"})
            return result.scalar() or 0
    except Exception as e:
        st.error(f"Error counting table metrics for {table_name}: {e}")
        return 0

def get_paginated_data(engine, table_name, page: int, page_size: int, search_term=""):
    """Fetches a single paginated slice of records from a specific table with optional search."""
    offset = (page - 1) * page_size
    
    try:
        with engine.connect() as conn:
            if not search_term:
                query = text(f"SELECT * FROM {table_name} LIMIT :limit OFFSET :offset;")
                df = pd.read_sql_query(query, conn, params={"limit": page_size, "offset": offset})
            else:
                # 🔍 SMART SEARCH: Search across all columns
                query = text(f"SELECT * FROM {table_name} WHERE ROW({table_name})::text ILIKE :search LIMIT :limit OFFSET :offset;")
                df = pd.read_sql_query(query, conn, params={"search": f"%{search_term}%", "limit": page_size, "offset": offset})
            return df
    except Exception as e:
        st.error(f"Error querying backend rows for {table_name}: {e}")
        return pd.DataFrame()

def render_dynamic_table(engine, table_name):
    """Renders a paginated, searchable data grid for ANY database table."""
    st.write("---")
    st.subheader(f"📊 Explorer: `{table_name}`")
    
    # 🔍 Smart Search Bar
    search_term = st.text_input(
        "🔍 Smart Search (filters any column on-the-fly):", 
        placeholder="Type essay ID, model name, persona, or any keyword...",
        key=f"search_{table_name}"
    )

    # 1. Initialize Pagination State values safely
    page_key = f"grid_page_{table_name}"
    if page_key not in st.session_state:
        st.session_state[page_key] = 1

    total_rows = get_total_row_count(engine, table_name, search_term)
    
    if total_rows == 0:
        if search_term:
            st.warning(f"No results found for '{search_term}'.")
        else:
            st.warning(f"⚠️ The table '{table_name}' appears empty.")
        return
    
    # Selection for rows per page
    page_size = st.select_slider(
        "📝 Rows per page:", 
        options=[5, 10, 25, 50, 100],
        value=10,
        key=f"size_{table_name}"
    )
    
    max_pages = max(1, (total_rows + page_size - 1) // page_size)
    
    # Safety clamp
    if st.session_state[page_key] > max_pages:
        st.session_state[page_key] = max_pages

    # 2. Pagination Controls
    col_prev, col_num, col_next = st.columns([1, 2, 1])
    
    with col_prev:
        if st.button("⬅️ Previous", key=f"prev_{table_name}", disabled=(st.session_state[page_key] <= 1), width="stretch"):
            st.session_state[page_key] -= 1
            st.rerun()
            
    with col_num:
        st.markdown(
            f"<p style='text-align: center; margin-top: 6px; font-size: 16px;'>"
            f"Page <b>{st.session_state[page_key]}</b> of {max_pages} <span style='color: #888;'>(Total Match: {total_rows})</span>"
            f"</p>", 
            unsafe_allow_html=True
        )
        
    with col_next:
        if st.button("Next ➡️", key=f"next_{table_name}", disabled=(st.session_state[page_key] >= max_pages), width="stretch"):
            st.session_state[page_key] += 1
            st.rerun()
            
    # 3. Fetch and Render
    df_page = get_paginated_data(engine, table_name, st.session_state[page_key], page_size, search_term)
    
    if not df_page.empty:
        # If 'id' exists, hide it for a cleaner look
        if 'id' in df_page.columns:
            df_display = df_page.drop(columns=['id'])
        else:
            df_display = df_page
            
        st.dataframe(df_display, width="stretch", hide_index=True)
    else:
        st.info("No data returned for this view.")