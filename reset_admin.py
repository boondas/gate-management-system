import psycopg2
from werkzeug.security import generate_password_hash
from urllib.parse import urlparse
import os
from dotenv import load_dotenv

load_dotenv()

def connect_to_database():
    url = urlparse(os.getenv("DATABASE_URL"))
    return psycopg2.connect(
        host=url.hostname,
        database=url.path[1:],
        user=url.username,
        password=url.password,
        port=url.port
    )

try:
    conn = connect_to_database()
    cursor = conn.cursor()
    new_password = "Admin123!"  # 👈 Change if you want
    hashed = generate_password_hash(new_password)

    cursor.execute("UPDATE admin_users SET password = %s WHERE username = 'admin'", (hashed,))
    conn.commit()
    conn.close()
    print("✅ Admin password reset successfully! Use:")
    print("   Username: admin")
    print(f"   Password: {new_password}")
except Exception as e:
    print("❌ Error:", e)
