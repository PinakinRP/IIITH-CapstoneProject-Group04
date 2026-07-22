import streamlit as st
import pages.home as home
from services.logging_service import Logger

st.set_page_config(
    page_title="Inventory System",
    page_icon="📦",
    layout="wide"
)

Logger.initialize()

home