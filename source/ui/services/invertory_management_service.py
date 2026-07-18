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

def search_products(search_text:str) -> pd.DataFrame:
    conn = sqlite3.connect(const.DB_FILE_PATH)
    query = """
        SELECT *
        FROM Product
        WHERE product_code LIKE ?
           OR product_name LIKE ?
        ORDER BY product_name;
    """
    search = search_text
    return pd.read_sql_query(
        query,
        conn,
        params=(search, search)
    )

def update_products(product_data:pd.DataFrame):
    conn = sqlite3.connect(const.DB_FILE_PATH)
    sql = """
        UPDATE Product
        SET
            product_category = ?,
            threshold = ?,
            unit_price = ?
        WHERE product_code = ?
    """

    data = [
        (
            row.product_category,
            row.threshold,
            row.unit_price,
            row.product_code,
        )
        for row in product_data.itertuples(index=False)
    ]

    conn.executemany(sql, data)
    conn.commit()

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
