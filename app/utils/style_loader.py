from pathlib import Path
import streamlit as st

def load_css():
    """Dynamically locates and injects theme.css regardless of which page calls it."""
    # __file__ is app/utils/style_loader.py
    # .parent is app/utils/
    # .parent.parent is app/
    css_path = Path(__file__).parent.parent / "styles" / "theme.css"
    arena_css_path = Path(__file__).parent.parent / "styles" / "arena.css"
    
    found_any = False
    for path in [css_path, arena_css_path]:
        if path.exists():
            found_any = True
            with open(path, "r", encoding="utf-8") as f:
                st.markdown(
                    f"<style>{f.read()}</style>",
                    unsafe_allow_html=True
                )
    
    if not found_any:
        # Subtle warning in case the file gets moved during development
        st.warning(f"CSS assets not detected in: {css_path.parent}")