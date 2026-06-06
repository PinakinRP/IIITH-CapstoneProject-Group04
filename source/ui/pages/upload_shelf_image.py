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
    base_df = st.session_state.processed_counts
    editor_state = st.session_state.get("inventory_from_photo", {})
    edited_rows = editor_state.get("edited_rows", {})
    
    if base_df is not None and not base_df.empty:
        final_df = base_df.copy()
        
        # Apply edits
        for row_idx, changes in edited_rows.items():
            if "New Stock" in changes:
                final_df.at[int(row_idx), "New Stock"] = changes["New Stock"]
        
        # Save to database
        update_inventory_for_products(final_df)
        st.session_state.success_message = "Inventory has been updated successfully"
        
        # FORCE FULL CLEANUP: Reset variables & bump key version to destroy widget cache
        st.session_state.processed_counts = None
        st.session_state.uploader_key_version += 1
        st.session_state.trigger_clean_rerun = True
    else:
        st.error("Nothing to update the inventory.")

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
            st.image(photo_uploaded, use_container_width=True)
            
        with product_count_grid_placeholder:
            st.divider()
            st.subheader("📝 Verify & Correct Detected Quantities")
            st.info("Double-click any number in the **New Stock** column to manually adjust AI miscounts.")
            
            st.data_editor(
                st.session_state.processed_counts,
                key="inventory_from_photo",
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Product Code": st.column_config.TextColumn(disabled=True),
                    "New Stock": st.column_config.NumberColumn(min_value=0, step=1, required=True)
                }
            )

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
