import streamlit as st
import pandas as pd
from components.sidebar import render_sidebar
import services.inventory_management_service as ims
import constants as const
from services.logging_service import Logger
import services.page_service as ps

def reset_session_state():
    st.session_state.search_results = None
    st.session_state.edited_data = None
    st.session_state.search_text = None
    st.session_state.manage_inventory_warning_message = ""

def render_styles():
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

def refresh_search_results():
    st.session_state.search_results = ims.search_products(st.session_state.search_text)

def render_search_bar():
    col1, col2 = st.columns([11,1])
    with col1:
        st.text_input("", placeholder="Enter Product Code Pattern or Product Name Pattern or % for all", key="search_text", label_visibility="collapsed")
    with col2:
        search_clicked = st.button("🔍 Search", type="primary")
    if search_clicked:
        if "search_text" not in st.session_state or st.session_state.search_text is None or st.session_state.search_text == "":
            st.error("Enter valid value in search box")
        else:
            st.session_state.search_results = ims.search_products(st.session_state.search_text)

def render_product_grid():
    if "search_results" in st.session_state and st.session_state.search_results is not None and not st.session_state.search_results.empty:
        st.subheader("Matching Products")
        st.session_state.edited_data = st.data_editor(
            st.session_state.search_results,
            disabled=[
                "product_code",
                "product_name",
                "quantity"
            ],
            use_container_width=True,
            hide_index=True,
            column_config={
                "product_code": "Product Code",
                "product_name": "Product Name",
                "product_category": "Category",
                "threshold": "Threshold Quantity",
                "quantity": "Available Quantity",
                "unit_price": "Price (₹)",
            }
        )

def render_save_button():
    if "edited_data" in st.session_state and st.session_state.edited_data is not None and not st.session_state.edited_data.empty:
        if st.button("💾 Update Product Data", use_container_width=True):
            with st.spinner("Updating the product data..."):
                try:
                    mask = (st.session_state.edited_data != st.session_state.search_results).any(axis=1)
                    changed = st.session_state.edited_data.loc[mask]
                    print(len(changed))
                    if not changed.empty:
                        ims.update_products(changed)
                        refresh_search_results()
                        st.toast("Products updated successfully.", icon="✅")
                    else:
                        st.toast("No changes to save", icon="⚠️")
                except Exception as ex:
                    print(f"ERROR: {ex}")
                    Logger.exception("Error occurred while saving the product data")
                    st.toast("Products update failed.", icon="❌")

def render_page():
    st.set_page_config(
        page_title="Product Setup",
        page_icon="🛍️",
        layout="wide"
    )

    render_sidebar()
    
    col1, col2 = st.columns([1, 11])
    with col1:
        st.image(
            str(const.IMAGE_DIR / "product-setup.png"), 
            use_container_width=True
        )
    with col2:
        st.header("Product Setup")

    render_styles()
    render_search_bar()
    render_product_grid()
    render_save_button() 

if not ps.is_postback(__file__):
    reset_session_state()
render_page()
