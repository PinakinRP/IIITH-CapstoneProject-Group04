import streamlit as st
from components.sidebar import render_sidebar
from pathlib import Path
from constants import IMAGE_DIR

def render_page():
    # --- PAGE CONFIGURATION ---
    st.set_page_config(page_title="Inventory System", page_icon="📦", layout="wide")

    render_sidebar()

    st.header("Welcome to Inventory System")
    st.write("The modern, smart, and effortless solution to manage your store's inventory.")
    st.write("---")

    # Features Grid Section
    st.header("What you can do")
    st.write("")
    
    #First row
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container(border=True):
            left_col, right_col = st.columns([1, 3])
            with left_col:
                st.image(
                    str(IMAGE_DIR / "smart-stock-tracking.png"), 
                    use_container_width=True
                )
            with right_col:
                st.subheader("Keep Inventory Updated")
                st.write("Upload the shelf and checkout images to update inventory.")
    with col2:
        with st.container(border=True):
            left_col, right_col = st.columns([1, 3])
            with left_col:
                st.image(
                    str(IMAGE_DIR / "ai-based-inventory-checking.png"), 
                    use_container_width=True
                )
            with right_col:
                st.subheader("Check Inventory")
                st.write("Get inventory related information using AI assistant.")

    # Second row
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container(border=True):
            left_col, right_col = st.columns([1, 3])
            with left_col:
                st.image(
                    str(IMAGE_DIR / "planogram-compliance.png"), 
                    use_container_width=True
                )
            with right_col:
                st.subheader("Check Planogram Compliance")
                st.write("Upload the shelf and planogram template images to check the compliance.")
if __name__ == "__main__":
    render_page()
