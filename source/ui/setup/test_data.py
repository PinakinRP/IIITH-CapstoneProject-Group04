import sqlite3
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import constants as const

# Connect to the database
conn = sqlite3.connect(const.DB_FILE_PATH)
cursor = conn.cursor()

# Query for 'Arridx' by joining Product and Inventory tables
select_sql = """
SELECT P.product_name, P.product_category, I.quantity
FROM Product P
JOIN Inventory I ON P.product_code = I.product_code
WHERE P.product_name = 'Arridx';
"""

cursor.execute(select_sql)
result = cursor.fetchone() # Fetch a single row

if result:
    product_name, product_category, quantity = result
    print(f"Inventory for {product_name}: {quantity} units. Category is {product_category}")
else:
    print("No inventory found for 'Arridx'.")

conn.close()