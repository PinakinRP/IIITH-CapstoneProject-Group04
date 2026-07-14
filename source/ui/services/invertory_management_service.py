import streamlit as st
from io import BytesIO
import pandas as pd
import constants as const
import sqlite3

# ------------------------------------------------------------------
# Sample Product Data
# Replace with database/API data
# ------------------------------------------------------------------
if "products" not in st.session_state:
    st.session_state.products = pd.DataFrame(columns=const.INVENTORY_COLUMNS)

def get_products(search_value):
    products = st.session_state.products
    if search_value.strip():
        result = products[
            products[const.INVENTORY_COLUMNS[0]].str.contains(search_value, case=False, na=False)
            |
            products[const.INVENTORY_COLUMNS[1]].str.contains(search_value, case=False, na=False)
        ]
    else:
        result = None
    return result

def add_product(p_code:str, p_name:str, p_stock:int) -> tuple[bool, str]:
    if not p_code or not p_code.strip():
        return False, f"{const.INVENTORY_COLUMNS[0]} required"
    if not p_name or not p_name.strip():
        return False, f"{const.INVENTORY_COLUMNS[1]} required"
    if p_stock < 0:
        return False, "Stock cannot be negative"
    
    df = st.session_state.products

    if p_code in df[const.INVENTORY_COLUMNS[0]].values:
        return False, "Product code already present. Search the product and then update it."
    elif p_name in df[const.INVENTORY_COLUMNS[1]].values:
        return False, "Product name already present. Search the product and then update it."
    else:
        # Insert a new row (fill missing columns with defaults or None)
        new_row = {const.INVENTORY_COLUMNS[0]: p_code.strip(), const.INVENTORY_COLUMNS[1]: p_name.strip(), const.INVENTORY_COLUMNS[2]: p_stock}
        st.session_state.products = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        return True, "Product added"

def delete_product(product_code:str):
    if product_code != None:
        st.session_state.products = st.session_state.products[
            st.session_state.products[const.INVENTORY_COLUMNS[0]] != product_code
        ]
        return 1
    else:
        return 0

def update_inventory(df_image_classification: pd.DataFrame, replace:bool):

    rows = list(df_image_classification.itertuples(index=False, name=None))
    conn = sqlite3.connect(const.DB_FILE_PATH)
    conn.executemany(f"""
        INSERT INTO Product (
            product_code,
            product_name,
            quantity
        )
        VALUES (?, ?, ?)
        ON CONFLICT(product_code)
        DO UPDATE SET
            product_name = excluded.product_name,
            quantity = {'' if replace else 'quantity - '}excluded.quantity
    """, rows)

    conn.commit()
