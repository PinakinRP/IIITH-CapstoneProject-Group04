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

def generate_invoice(item_details:pd.DataFrame) -> pd.DataFrame:
    product_codes = tuple(item_details[const.IMAGE_CLASSIFICATION_COLUMNS[0]].tolist())
    df_prices = get_unit_prices(product_codes)
    if df_prices is not None and not df_prices.empty:

        df_combined = item_details.merge(df_prices, on=const.IMAGE_CLASSIFICATION_COLUMNS[0], how='left')
        df_combined[const.INVOICE_COLUMNS[2]] = pd.to_numeric(df_combined[const.INVOICE_COLUMNS[2]], errors='coerce').fillna(0)
        df_combined[const.INVOICE_COLUMNS[3]] = pd.to_numeric(df_combined[const.INVOICE_COLUMNS[3]], errors='coerce').fillna(0.0)
        df_combined[const.INVOICE_COLUMNS[4]] = df_combined[const.INVOICE_COLUMNS[2]] * df_combined[const.INVOICE_COLUMNS[3]]
    else:
        df_combined = item_details.copy()
        df_combined[const.INVOICE_COLUMNS[3]] = 0.0
        df_combined[const.INVOICE_COLUMNS[4]] = 0.0
    return df_combined

def get_unit_prices(item_codes:tuple) -> pd.DataFrame:
    conn = sqlite3.connect(const.DB_FILE_PATH) 
    try:
        query = f"SELECT product_code AS [{const.INVOICE_COLUMNS[0]}], unit_price AS [{const.INVOICE_COLUMNS[3]}] FROM product WHERE product_code IN {item_codes}"
        return pd.read_sql_query(query, conn, dtype={
            const.INVOICE_COLUMNS[0]: 'string',
            const.INVOICE_COLUMNS[3]: 'float64'
        })
    finally:
        conn.close()
    return None

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
            quantity = {'' if replace else 'quantity + '}excluded.quantity
    """, rows)

    conn.commit()
