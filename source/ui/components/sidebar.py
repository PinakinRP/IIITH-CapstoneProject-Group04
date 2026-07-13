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
    st.sidebar.page_link("pages/home.py", label="🏠 Home")
    st.sidebar.page_link("pages/ai_assistant.py", label="🤖 AI Assistant")
    st.sidebar.page_link("pages/upload_shelf_image.py", label="📷 Update Inventory")
    st.sidebar.page_link("pages/planogram_compliance.py", label="🧩 Check Planogram Compliance")
    st.sidebar.page_link("pages/upload_checkout_image.py", label="🛒 Checkout Items")