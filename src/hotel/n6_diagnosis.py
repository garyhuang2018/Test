import os
import sqlite3

# Define the path to the file using a raw string
file_path = r'D:\11_客诉分析\0_过往客诉转用例\n6-logs\gateway.db'

# Check if the file exists
if not os.path.exists(file_path):
    print(f"Error: File {file_path} does not exist.")
    exit()

# Connect to the SQLite database
conn = sqlite3.connect(file_path)
cursor = conn.cursor()

# Execute a query to retrieve data from the database
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("Tables in the database:")
for table in tables:
    print(table[0])

# Optionally, read data from a specific table
# Replace 'your_table_name' with the actual table name
table_name = 'rcu_scene'
cursor.execute(f"SELECT * FROM {table_name};")
rows = cursor.fetchall()

print(f"\nData from table {table_name}:")
for row in rows:
    print(row)

# Close the connection
conn.close()