import streamlit as st

from utils.style_loader import load_css
from components.info_cards import info_card, info_card_LLMs
from templates.home import render_home
from templates.side_bar import render_sidebar