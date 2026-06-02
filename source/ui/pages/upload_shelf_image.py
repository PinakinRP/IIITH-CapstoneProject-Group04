import streamlit as st
from components.sidebar import render_sidebar
from services.invertory_management_service import update_inventory_using_shelf_photo

st.set_page_config(
    page_title="Upload Shelf Image",
    page_icon="📷",
    layout="wide"
)

render_sidebar()

st.title("📷 Upload Shelf Photo")

st.write("Upload a shelf photo to update inventory.")

uploaded_file = st.file_uploader(
    "Choose the photo",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file:
    st.image(uploaded_file, use_container_width=True)

    if st.button("Update Inventory"):
        update_inventory_using_shelf_photo(uploaded_file)
        st.success("Inventory is updated successfully.")