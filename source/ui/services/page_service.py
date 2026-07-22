import streamlit as st

def is_postback(page_name:str) -> bool:
    result = ("current_page" in st.session_state and st.session_state.current_page == page_name)
    if not result:
        set_current_page(page_name)
    return result

def set_current_page(page_name:str):
    st.session_state.current_page = page_name