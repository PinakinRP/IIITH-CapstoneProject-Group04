import streamlit as st
import pandas as pd
from components.sidebar import render_sidebar
import services.invertory_management_service as ims

def initialize_session_state():
    if "search_results" not in st.session_state:
        st.session_state.search_results = pd.DataFrame()

    if "new_stock_values" not in st.session_state:
        st.session_state.new_stock_values = {}

    if "search_text" not in st.session_state:
        st.session_state.search_text = ""

def reset_page_state():
    st.session_state.search_results = pd.DataFrame()
    st.session_state.new_stock_values = {}

def refresh_search_results():
    reset_page_state()
    # Fix: Safely reads the text input directly from the state dictionary
    clean_text = st.session_state.search_text.strip()
    st.session_state.search_results = ims.get_products(clean_text)

def show_search_bar():
    # Fix: Tied directly to session state key. No 'global' keyword needed.
    search_container.text_input(
        "Enter Product Code or Product Name",
        placeholder="Search product...",
        key="search_text" 
    )

    search_clicked = search_container.button("Search", type="primary")

    if search_clicked:
        refresh_search_results()

def update_stock():
    # Update backend database
    ims.update_inventory_for_products(pd.DataFrame(
        st.session_state.new_stock_values.items(),
        columns=["Product Code", "New Stock"]))
    
    # Pull fresh database values immediately using state variable
    clean_text = st.session_state.search_text.strip()
    st.session_state.search_results = ims.get_products(clean_text)

    # Clear temporary tracked changes
    st.session_state.new_stock_values = {}
    
    save_button_message.success("Stock updated successfully")

def delete_product(p_code: str):
    if ims.delete_product(p_code) == 1:
        st.session_state.search_results = st.session_state.search_results[
            st.session_state.search_results["Product Code"] != p_code
        ]
        refresh_search_results()
        save_button_message.success("Product removed successfully.")

def show_products_grid():
    if st.session_state.search_results is None or st.session_state.search_results.empty:
        return
    
    grid_container.divider()
    grid_container.subheader("Update Inventory")

    # Save button
    save_button_container.button("Save Stock Changes", on_click=update_stock)
    
    # Render the grid inside the grid_container placeholder
    with grid_container:
        column_size = [2, 4, 1, 1, 1]
        # Header
        header_cols = st.columns(column_size)
        header_cols[0].markdown("**Product Code**")
        header_cols[1].markdown("**Product Name**")
        header_cols[2].markdown("**Current Stock**")
        header_cols[3].markdown("**New Stock**")
        header_cols[4].markdown("**Delete**")

        # Rows
        for idx, row in st.session_state.search_results.iterrows():
            cols = st.columns(column_size)
            p_code = row["Product Code"]
            p_stock = row["Current Stock"]

            cols[0].write(p_code)
            cols[1].write(row["Product Name"])
            cols[2].write(p_stock)

            new_stock = cols[3].number_input(
                label="new_stock",
                label_visibility="collapsed",
                min_value=0,
                value=p_stock,
                step=1,
                key=f"new_stock_{p_code}"
            )
            st.session_state.new_stock_values[p_code] = new_stock

            # Fix: Wrapped p_code into a valid single-item Python tuple using a comma
            cols[4].button(
                "🗑️",
                key=f"delete_{p_code}",
                on_click=delete_product,
                args=(p_code,) 
            )

def add_product(p_code: str, p_name: str, p_stock: int):
    is_success, message = ims.add_product(p_code, p_name, p_stock)
    if is_success:
        refresh_search_results()
        add_product_container.success(message)
    else:
        add_product_container.error(message)

def show_add_product_form():
    add_product_container.divider()
    add_product_container.subheader("Add Product")
    with add_product_container:
        column_size = [2, 4, 1, 1, 1]
        # Header
        header_cols = st.columns(column_size)
        header_cols[0].markdown("**Product Code**")
        header_cols[1].markdown("**Product Name**")
        header_cols[2].markdown("**Stock**")
        cols = st.columns(column_size)
        # Detail
        p_code = cols[0].text_input(
            label="product_code",
            label_visibility="collapsed"
        )
        p_name = cols[1].text_input(
            label="product_name",
            label_visibility="collapsed"
        )
        p_stock = cols[2].number_input(
            label="product_stock",
            label_visibility="collapsed",
            min_value=0,
            value=0,
            step=1,
            key="product_stock"
        )

    add_product_container.button("Add Product",
                                 on_click=add_product,
                                 args=(p_code, p_name, p_stock))

def render_page():
    global search_container, grid_container, save_button_container, save_button_message, add_product_container
    
    initialize_session_state()

    st.set_page_config(
        page_title="Manage Inventory",
        page_icon="📦",
        layout="wide"
    )

    render_sidebar()
    st.title("📦 Manage Inventory")

    # Create layout placeholders
    search_container = st.container()
    grid_container = st.container(key="search_results")
    save_button_container = st.container()
    save_button_message = st.container()
    add_product_container = st.container()

    show_search_bar()
    show_products_grid()
    show_add_product_form()

if __name__ == "__main__":
    render_page()
