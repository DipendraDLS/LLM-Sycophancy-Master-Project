import json
import pandas as pd
from sqlalchemy import text
from .connect_db import engine, PROJECT_ROOT
from .models import Base, Essay, create_dynamic_response_model


def provision_essays_table(csv_file_name="essay_dataset.csv"):
    """Reads the dataset csv and pushes it into postgres tables if they are empty."""
    import os
    csv_path = os.path.join(PROJECT_ROOT, "data", "dataset", csv_file_name)
    
    if not os.path.exists(csv_path):
        # We don't want to crash if files aren't in place yet, just log for the user/UI
        print(f"Source dataset CSV not found at: {csv_path}. Skipping essays provision.")
        return
        
    # Build tables using SQLAlchemy blueprints
    Base.metadata.create_all(engine)
    
    # Check if data already exists to prevent duplicate insertion
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {Essay.__tablename__};"))
            if result.scalar() > 0:
                return  # Database is already populated
    except Exception:
        pass 

    # Read and clean CSV structure
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.replace(' ', '_').str.lower()
    
    # Match exact column constraints
    target_columns = ['essay_id', 'prompt_name', 'human_score', 'content']
    df = df[[col for col in target_columns if col in df.columns]]
    
    # Append records directly
    df.to_sql(Essay.__tablename__, engine, if_exists='append', index=False)
    print(f"Successfully provisioned '{Essay.__tablename__}' table.")

def provision_json_dataset(json_file_name="full_run_llm_response_original.json"):
    """Loads a run result JSON from data/dataset/ into the database if it exists."""
    import os
    json_path = os.path.join(PROJECT_ROOT, "data", "dataset", json_file_name)
    
    if not os.path.exists(json_path):
        # Skip gracefully if user hasn't copied the file yet
        print(f"Optional dataset '{json_file_name}' not found at {json_path}. Skipping.")
        return

    # Derive table name from filename (strip path and extension)
    table_name = os.path.splitext(os.path.basename(json_path))[0]
    
    # Use the dynamic model factory to ensure schema matches experiment results
    DynamicModelClass = create_dynamic_response_model(table_name)
    Base.metadata.create_all(bind=engine, tables=[DynamicModelClass.__table__])
    
    # Check if data already exists
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name};"))
            if result.scalar() > 0:
                return  # Database is already populated
    except Exception:
        pass

    # Load JSON and push to SQL
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
            if not data:
                return
            
            df = pd.DataFrame(data)
            df.to_sql(table_name, engine, if_exists='append', index=False)
            print(f"Successfully provisioned '{table_name}' table from JSON.")
    except Exception as e:
        print(f"Error loading JSON dataset '{json_file_name}': {e}")