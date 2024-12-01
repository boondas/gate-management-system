import sqlite3

# Connect to the database (or create it if it doesn't exist)
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Create the table to store phone numbers
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone_number TEXT UNIQUE
)
""")
conn.commit()
conn.close()
print("Database and table created successfully!")
