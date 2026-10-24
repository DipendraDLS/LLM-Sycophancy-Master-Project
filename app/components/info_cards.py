from components.package_loader import *

def info_card(title: str, content: str):
    card_html = f"""
    <div class="custom-card">
        <div class="card-title">{title}</div>
        <div class="card-subtitle">{content}</div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)



def info_card_LLMs(title, text, url=None, max_length=50):
    # 1. Process the text truncation logic exactly how you designed it
    if len(text) > max_length and url:
        display_text = f'{text[:max_length].strip()}...'
    else:
        display_text = text

    # 2. Build the inline link if a URL is provided
    link_html = ""
    if url:
        link_html = f' <a href="{url}" target="_blank" class="card-link">Click here</a>'

    # 3. Inject the CSS styles and structure the final HTML container
    card_html = f"""
    <div class="custom-card">
        <div class="card-title">{title}</div>
        <div class="card-body">
            {display_text}{link_html}
        </div>
    </div>
    """
    
    # 4. Render the unified component
    st.markdown(card_html, unsafe_allow_html=True)