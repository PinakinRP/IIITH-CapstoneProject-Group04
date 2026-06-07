import streamlit as st
import pandas as pd
from components.sidebar import render_sidebar
from services.invertory_management_service import update_inventory_for_products
from services.image_processing_service import get_product_counts

def initialize_session_state():
    # --- Initialize Persistent Variables ---
    if "processed_counts" not in st.session_state:
        st.session_state.processed_counts = None

    if "uploader_key_version" not in st.session_state:
        st.session_state.uploader_key_version = 0

def update_inventory():
    # Save to database
    update_inventory_for_products(st.session_state.processed_counts)
    st.session_state.success_message = "Inventory has been updated successfully"
    
    # FORCE FULL CLEANUP: Reset variables & bump key version to destroy widget cache
    st.session_state.processed_counts = None
    st.session_state.uploader_key_version += 1
    st.session_state.trigger_clean_rerun = True

def render_page():
    initialize_session_state()
    
    st.set_page_config(
        page_title="Upload Shelf Image",
        page_icon="📷",
        layout="wide"
    )

    render_sidebar()

    # Layout Containers
    upload_photo_container = st.container()
    product_count_grid_placeholder = st.container()

    # --- Clear State Rerun Interceptor ---
    if st.session_state.get("trigger_clean_rerun", False):
        st.session_state.trigger_clean_rerun = False
        st.rerun()

    # Display banner safely post-rerun
    if "success_message" in st.session_state and st.session_state.success_message:
        st.success(st.session_state.success_message)
        st.session_state.success_message = None

    # --- Render Form Layout Natively ---
    upload_photo_container.title("📷 Upload Shelf Photo")
    upload_photo_container.write("Upload a shelf photo to update inventory.")

    # Dynamic key rotation format string
    active_uploader_key = f"shelf_photo_v{st.session_state.uploader_key_version}"

    photo_uploaded = upload_photo_container.file_uploader(
        "Choose the photo",
        key=active_uploader_key,
        type=["jpg", "jpeg", "png"]
    )

    # --- Inline Main Processing Track (Replaces on_change) ---
    if photo_uploaded is not None:
        # Trigger image calculation only if we don't have results stored yet
        if st.session_state.processed_counts is None:
            with st.spinner("Processing shelf image analytics..."):
                raw_counts = get_product_counts(photo_uploaded)
                if isinstance(raw_counts, dict):
                    st.session_state.processed_counts = pd.DataFrame(
                        list(raw_counts.items()), 
                        columns=["Product Code", "New Stock"]
                    )
                else:
                    st.session_state.processed_counts = raw_counts
                st.rerun() # Refresh to populate layout grids smoothly

        # Display components on screen safely
        with upload_photo_container:
            st.image(photo_uploaded, width=300)
            
        with product_count_grid_placeholder:
            st.divider()
            st.subheader("📝 Detected Products & Quantities")
            
            column_size = [5, 1, 1]

            # Header
            header_cols = st.columns(column_size)
            header_cols[0].markdown("**Product Code**")
            header_cols[1].markdown("**Detected Quantity**")
            header_cols[2].markdown("**Corrected Quantity**")

            # Rows
            for idx, row in st.session_state.processed_counts.iterrows():
                cols = st.columns(column_size)
                p_code = row["Product Code"]
                d_stock = row["New Stock"]

                cols[0].write(p_code)
                cols[1].write(d_stock)
                c_stock = cols[2].number_input(
                    label="corrected_stock",
                    label_visibility="collapsed",
                    min_value=0,
                    value=d_stock,
                    step=1,
                    key=f"corrected_stock_{p_code}"
                )
                df = st.session_state.processed_counts
                df.loc[df["Product Code"] == p_code, "New Stock"] = c_stock

            st.button(
                "Update Inventory",
                type="primary",
                on_click=update_inventory
            )
    else:
        # If the user clicks the small close "X" manually on the widget, clear calculations
        st.session_state.processed_counts = None

if __name__ == "__main__":
    render_page()
