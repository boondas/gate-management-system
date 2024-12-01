import psycopg2

# Database connection
conn = psycopg2.connect(
    host="localhost",
    database="gate_management",
    user="postgres",
    password="yourpassword"
)

def get_all_users():
    with conn.cursor() as cur:
        cur.execute("SELECT id, name, phone_number, access FROM users")
        return cur.fetchall()

def add_user(name, phone, access):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO users (name, phone_number, access) VALUES (%s, %s, %s)",
            (name, phone, access),
        )
        conn.commit()

def update_user(id, name, phone, access):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE users SET name = %s, phone_number = %s, access = %s WHERE id = %s",
            (name, phone, access, id),
        )
        conn.commit()

def delete_user(id):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM users WHERE id = %s", (id,))
        conn.commit()

def get_user_by_id(id):
    with conn.cursor() as cur:
        cur.execute("SELECT id, name, phone_number, access FROM users WHERE id = %s", (id,))
        return cur.fetchone()
