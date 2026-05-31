import streamlit as st
import pandas as pd
from components.sidebar import render_sidebar

st.set_page_config(
    page_title="Manage Inventory",
    page_icon="📦",
    layout="wide"
)

render_sidebar()

st.title("📦 Manage Inventory")

# Sample inventory
df = pd.DataFrame({
    "Product": ["Coke", "Pepsi", "Sprite"],
    "Stock": [120, 90, 60]
})

st.dataframe(df, use_container_width=True)

st.divider()

st.subheader("Add New Product")

col1, col2 = st.columns(2)

with col1:
    product = st.text_input("Product Name")

with col2:
    stock = st.number_input("Stock", min_value=0)

if st.button("Add Product"):
    st.success(f"Added {product} with stock {stock}")