import streamlit as st
import pages.home as home

st.set_page_config(
    page_title="Inventory System",
    page_icon="📦",
    layout="wide"
)

home.render_page()