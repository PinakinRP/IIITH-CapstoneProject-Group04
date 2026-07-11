import sqlite3

# Connect to the database
conn = sqlite3.connect('inventory.db')
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