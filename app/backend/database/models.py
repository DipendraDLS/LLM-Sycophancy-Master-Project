from sqlalchemy import Column, Text, Numeric, Integer, String, Float
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Essay(Base):
    __tablename__ = 'essays'
    
    # THE FIX: A dedicated, auto-incrementing primary key for the database
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Now essay_id can repeat safely as many times as the CSV requires!
    essay_id = Column(Text, nullable=False) 
    prompt_name = Column(Text, nullable=True)
    human_score = Column(Numeric, nullable=True)
    content = Column(Text, nullable=False)

def get_llm_response_table_metadata(table_name: str):
    """
    Dynamically generates columns for an independent database table 
    keyed specifically to an experiment execution timestamp.
    """
    return {
        "__tablename__": table_name,
        "id": Column(Integer, primary_key=True, autoincrement=True),
        "model": Column(String(100), nullable=False),
        "essay_id": Column(Integer, nullable=False),
        "human_score": Column(Float, nullable=True),
        "persona": Column(String(100), nullable=False),
        "pushback": Column(String(100), nullable=False),
        "pushback_direction": Column(String(50), nullable=True),
        
        # Turn 0 (Baseline)
        "score_baseline": Column(Float, nullable=True),
        "justification_baseline": Column(Text, nullable=True),
        
        # Multi-turn automated pushbacks
        "score_turn1": Column(Float, nullable=True),
        "justification_turn1": Column(Text, nullable=True),
        "pushback_turn1": Column(Text, nullable=True),
        
        "score_turn2": Column(Float, nullable=True),
        "justification_turn2": Column(Text, nullable=True),
        "pushback_turn2": Column(Text, nullable=True),
        
        "score_turn3": Column(Float, nullable=True),
        "justification_turn3": Column(Text, nullable=True),
        "pushback_turn3": Column(Text, nullable=True),
    }

# Global registry for dynamically created models to prevent SQLAlchemy registration conflicts
_dynamic_model_cache = {}

def create_dynamic_response_model(table_name: str):
    """
    Factory creating distinct model classes bound to custom tracking sessions.
    """
    #THE FIX: Convert table name prefixes into a safe Python Class name format.
    safe_class_name = f"{table_name}".replace("-", "_").replace(".", "_")
    
    # If this model was already created in this process session, return the cached version
    if safe_class_name in _dynamic_model_cache:
        return _dynamic_model_cache[safe_class_name]

    attrs = get_llm_response_table_metadata(table_name)
    DynamicModel = type(safe_class_name, (Base,), attrs)
    
    # Store in cache for future calls (e.g. database restarts)
    _dynamic_model_cache[safe_class_name] = DynamicModel
    
    return DynamicModel