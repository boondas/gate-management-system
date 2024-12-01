import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Add authorized numbers
authorized_numbers = [
    ("0786384899",),
    ("+0987654321",)
]
cursor.executemany("INSERT OR IGNORE INTO users (phone_number) VALUES (?)", authorized_numbers)
conn.commit()
conn.close()
print("Test data added successfully!")
