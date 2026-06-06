import streamlit as st
import pages.ai_assistant as assistant

st.set_page_config(
    page_title="Inventory System",
    page_icon="📦",
    layout="wide"
)

assistant.render_page()