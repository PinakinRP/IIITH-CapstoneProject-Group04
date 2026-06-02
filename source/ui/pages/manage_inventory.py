import streamlit as st
import pandas as pd
from components.sidebar import render_sidebar
import services.invertory_management_service as ims

search_text = None

# --- Initialize Session State Variables ---
if "search_results" not in st.session_state:
    st.session_state.search_results = pd.DataFrame()

if "new_stock_values" not in st.session_state:
    st.session_state.new_stock_values = {}

def reset_page_state():
    st.session_state.search_results = pd.DataFrame()
    st.session_state.new_stock_values = {}

def refresh_search_results():
    reset_page_state()
    st.session_state.search_results = ims.get_products(search_text.strip())

def show_search_bar():
    global search_text
    # Search Section
    search_text = search_container.text_input(
        "Enter Product Code or Product Name",
        placeholder="Search product..."
    )

    search_clicked = search_container.button("Search", type="primary")

    if search_clicked:
        refresh_search_results()

def show_products_grid():
    global search_text
    if st.session_state.search_results.empty:
        return
    
    grid_container.divider()
    grid_container.subheader("Update Inventory")
    if st.session_state.search_results.empty:
        grid_container.text("No product found")
        return

    # 2. Process Save Action BEFORE Rendering Rows (but below the placeholders)
    # The button itself sits naturally at the bottom of this code section
    save_stock_changes = save_button_container.button("Save Stock Changes")
    if save_stock_changes:
        # Update backend database
        ims.update_invetory_for_products(st.session_state.new_stock_values)
        
        # Pull fresh database values immediately
        st.session_state.search_results = ims.get_products(search_text.strip())

        # Clear temporary tracked changes
        st.session_state.new_stock_values = {}
        
        save_button_message.success("Stock updated successfully")
        st.rerun()


    # 3. Render the grid inside the grid_container placeholder
    with grid_container:
        column_size = [2,4,1,1,1]
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

            delete_product = cols[4].button(
                "🗑️",
                key=f"delete_{p_code}"
            )
            
            if delete_product:
                if ims.delete_product(p_code) == 1:
                    st.session_state.search_results = st.session_state.search_results[
                        st.session_state.search_results["Product Code"] != p_code
                    ]
                    refresh_search_results()
                    # Send the success message backward in time to the top container
                    save_button_message.success("Product removed successfully.")
                    st.rerun()

def show_add_product_form():
    add_product_container.divider()
    add_product_container.subheader("Add Product")
    with add_product_container:
        column_size = [2,4,1,1,1]
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

    add_product = add_product_container.button("Add Product")

    if add_product:
        is_success, message = ims.add_product(p_code, p_name, p_stock)

        if is_success:
            refresh_search_results()
            add_product_container.success(message)
            st.rerun()
        else:
            add_product_container.error(message)

## Main code
st.set_page_config(
    page_title="Manage Inventory",
    page_icon="📦",
    layout="wide"
)

render_sidebar()
st.title("📦 Manage Inventory")

# 1. Create layout placeholders (Grid space is allocated first)
search_container = st.container()
grid_container = st.container()
save_button_container = st.container()
save_button_message = st.container()
add_product_container = st.container()

show_search_bar()
show_products_grid()
show_add_product_form()
