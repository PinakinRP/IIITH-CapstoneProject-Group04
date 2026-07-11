import sqlite3

# Connect to the database
conn = sqlite3.connect('inventory.db')
cursor = conn.cursor()

try:

    # Insert some Deos in product with default threshold and quantity
    cursor.execute("""
        INSERT INTO Product (product_code, product_name, product_category, threshold, quantity)
        VALUES ('D0', 'Arridx', 'Deo', 3, 8);
    """)
    cursor.execute("""
        INSERT INTO Product (product_code, product_name, product_category, threshold, quantity)
        VALUES ('D1', 'Degree', 'Deo', 3, 5);
    """)
    cursor.execute("""
        INSERT INTO Product (product_code, product_name, product_category, threshold, quantity)
        VALUES ('D2', 'Dove', 'Deo', 3, 2);
    """)
    cursor.execute("""
        INSERT INTO Product (product_code, product_name, product_category, threshold, quantity)
        VALUES ('D3', 'Mitchum', 'Deo', 3, 0);
    """)
    # Insert Deos in inventory
    cursor.execute("""
        INSERT INTO Inventory (id, product_code, shelf, quantity)
        VALUES ('inv_001', 'D0', 1, 5);
    """)
    cursor.execute("""
        INSERT INTO Inventory (id, product_code, shelf, quantity)
        VALUES ('inv_002', 'D0', 3, 3);
    """)
    cursor.execute("""
        INSERT INTO Inventory (id, product_code, shelf, quantity)
        VALUES ('inv_003', 'D1', 3, 5);
    """)
    cursor.execute("""
        INSERT INTO Inventory (id, product_code, shelf, quantity)
        VALUES ('inv_004', 'D2', 2, 2);
    """)

    conn.commit()
    print("Records for Deos inserted successfully.")
except sqlite3.IntegrityError as e:
    print(f"Error inserting record: {e}. It might already exist if you run this multiple times.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
finally:
    conn.close()