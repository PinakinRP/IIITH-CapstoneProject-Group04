import streamlit as st
from components.sidebar import render_sidebar
import constants as const
from pathlib import Path
import services.page_service as ps 

def render_style():
    st.markdown("""
    <style>
        div.stButton > button {
            background-color: #A4E9FF;
            border-color: #A4E9FF;
        }            

        div.stButton > button:hover {
            background-color: #A4E9FF;
            border-color: #A4E9FF;
        } 
                    
        div.stButton > button p {
            color: #1A1A1A;
        }
    </style>
    """, unsafe_allow_html=True)

def render_page():
    # --- PAGE CONFIGURATION ---
    st.set_page_config(
        page_title="Application Log",
        page_icon="📋",
        layout="wide"
    )

    render_sidebar()
    render_style()

    col1, col2, col3 = st.columns([1, 10, 1])
    with col1:
        st.image(
            str(const.IMAGE_DIR / "application-log.png"), 
            use_container_width=True
        )
    with col2:
        st.header("Application Logs")
    with col3:
        if st.button("⟳ Refresh"):
            st.rerun()

    log_file = Path(const.LOGGING_FILE)

    with st.container(border=True, width="stretch"):
        if log_file.exists():
            log_text = log_file.read_text()
            if log_text is not None and len(log_text) > 0:
                st.code(log_file.read_text(), language="text")
            else:
                st.info("Empty file.")
        else:
            st.info("No log file found.")

ps.set_current_page(__file__)
render_page()
