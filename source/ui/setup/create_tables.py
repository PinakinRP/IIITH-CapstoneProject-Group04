import sqlite3
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import constants as const

# Connect to an SQLite database (this will create the file if it doesn't exist)
# The database will be created in the Colab environment.
#conn = sqlite3.connect('inventory.db')
conn = sqlite3.connect(const.DB_FILE_PATH)
cursor = conn.cursor()

for table in ["Inventory", "Product"]:
    cursor.execute(f"DROP TABLE IF EXISTS {table};")

# Define the SQL statement to create the 'Product' table
create_product_table_sql = """
CREATE TABLE IF NOT EXISTS Product (
    product_code TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    product_category TEXT NULL,
    threshold INTEGER DEFAULT 3,
    quantity INTEGER DEFAULT 0
);
"""
cursor.execute(create_product_table_sql)

# Define the SQL statement to create the 'Inventory' table with a foreign key
create_inventory_table_sql = """
CREATE TABLE IF NOT EXISTS Inventory (
    id TEXT PRIMARY KEY,
    product_code TEXT NOT NULL,
    shelf INTEGER,
    quantity INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (product_code) REFERENCES Product(product_code)
);
"""
cursor.execute(create_inventory_table_sql)

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Database 'inventory.db' created and 'Product' and 'Inventory' tables initialized.")