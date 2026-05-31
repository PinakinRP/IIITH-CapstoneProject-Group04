import streamlit as st
from components.sidebar import render_sidebar

st.set_page_config(
    page_title="Upload Shelf Image",
    page_icon="📷",
    layout="wide"
)

render_sidebar()

st.title("📷 Upload Shelf Image")

st.write("Upload a shelf image for processing.")

uploaded_file = st.file_uploader(
    "Choose an image",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file:
    st.image(uploaded_file, use_container_width=True)

    if st.button("Analyze Image"):
        st.success("Image uploaded successfully and sent for analysis.")