import streamlit as st

def render_sidebar():
    st.markdown("""
<style>
[data-testid="stSidebarNav"] {
    display: none;
}
</style>
""", unsafe_allow_html=True)
    
    st.sidebar.title("📦 Inventory System")

    # Sidebar navigation links
    st.sidebar.page_link("pages/ai_assistant.py", label="🤖 AI Assistant")
    st.sidebar.page_link("pages/upload_shelf_image.py", label="📷 Upload Shelf Image")
    st.sidebar.page_link("pages/manage_inventory.py", label="📦 Manage Inventory")