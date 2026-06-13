import streamlit as st
from io import BytesIO
import pandas as pd

# ------------------------------------------------------------------
# Sample Product Data
# Replace with database/API data
# ------------------------------------------------------------------
if "products" not in st.session_state:
    st.session_state.products = pd.DataFrame(
        [
            {"Shelf Id": "Refreshments", "Product Code": "BEV000001", "Product Name": "Coke", "Current Stock": 25},
            {"Shelf Id": "Refreshments", "Product Code": "BEV000002", "Product Name": "Sprite", "Current Stock": 120},
            {"Shelf Id": "Refreshments", "Product Code": "BEV000003", "Product Name": "Appy", "Current Stock": 80},
            {"Shelf Id": "Refreshments", "Product Code": "BEV000004", "Product Name": "Campa", "Current Stock": 35},
        ]
    )

def get_products(search_value):
    products = st.session_state.products
    if search_value.strip():
        result = products[
            products["Product Code"].str.contains(search_value, case=False, na=False)
            |
            products["Product Name"].str.contains(search_value, case=False, na=False)
        ]
    else:
        result = None
    return result

def add_product(p_code:str, p_name:str, shelf_id:str, p_stock:int) -> tuple[bool, str]:
    if not p_code or not p_code.strip():
        return False, "Product code required"
    if not p_name or not p_name.strip():
        return False, "Product name required"
    if not shelf_id or not shelf_id.strip():
        return False, "Shelf required"
    if p_stock < 0:
        return False, "Stock cannot be negative"
    
    df = st.session_state.products

    if p_code in df["Product Code"].values:
        return False, "Product code already present. Search the product and then update it."
    elif p_name in df["Product Name"].values:
        return False, "Product name already present. Search the product and then update it."
    else:
        # Insert a new row (fill missing columns with defaults or None)
        new_row = {"Product Code": p_code.strip(), "Product Name": p_name.strip(), "Shelf Id": shelf_id, "Current Stock": p_stock}
        st.session_state.products = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        return True, "Product added"

def update_inventory_using_shelf_photo(uploaded_file:BytesIO):
    pass

def delete_product(product_code:str):
    if product_code != None:
        st.session_state.products = st.session_state.products[
            st.session_state.products["Product Code"] != product_code
        ]
        return 1
    else:
        return 0

def update_inventory_for_products(new_stock_dataframe: pd.DataFrame) -> dict:
    update_count = {}
    for idx, row in new_stock_dataframe.iterrows():
        sku = row["Product Code"]
        new_stock = row["New Stock"]
        
        # Locate the product row in master database state
        mask = (
            st.session_state.products["Product Code"]
            .astype(str)
            .str.strip()
            .str.casefold()
            == str(sku).strip().casefold()
        )
        
        # Overwrite the stock value safely
        st.session_state.products.loc[mask, "Current Stock"] = new_stock

        update_count[sku] = mask.sum()
    return update_count
