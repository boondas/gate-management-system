from flask import Flask, jsonify, request, render_template, redirect
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# Database connection URL (from environment variable)
DATABASE_URL = os.getenv("DATABASE_URL")


# Function to establish database connection
def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require', cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None


# API: Root endpoint
@app.route("/")
def index():
    return jsonify({"message": "Welcome to the Gate Management System API!"})


# API: Add a phone number
@app.route("/add", methods=["POST"])
def add_phone_number():
    try:
        data = request.json
        phone_number = data.get("phone_number")

        if not phone_number:
            return jsonify({"error": "Phone number is required"}), 400

        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO authorized_users (phone_number) VALUES (%s)", (phone_number,))
            conn.commit()
            cur.close()
            conn.close()
            return jsonify({"message": "Phone number added successfully"}), 201
        else:
            return jsonify({"error": "Database connection error"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# API: Remove a phone number
@app.route("/remove", methods=["DELETE"])
def remove_phone_number():
    try:
        data = request.json
        phone_number = data.get("phone_number")

        if not phone_number:
            return jsonify({"error": "Phone number is required"}), 400

        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM authorized_users WHERE phone_number = %s", (phone_number,))
            conn.commit()
            cur.close()
            conn.close()
            return jsonify({"message": "Phone number removed successfully"}), 200
        else:
            return jsonify({"error": "Database connection error"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# API: List all phone numbers
@app.route("/list", methods=["GET"])
def list_phone_numbers():
    try:
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT phone_number FROM authorized_users")
            phone_numbers = cur.fetchall()
            cur.close()
            conn.close()
            return jsonify({"phone_numbers": phone_numbers}), 200
        else:
            return jsonify({"error": "Database connection error"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Web Interface: Main page
@app.route("/web")
def web_index():
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("SELECT id, phone_number, name, access FROM authorized_users")
        users = cur.fetchall()
        cur.close()
        conn.close()
        return render_template("index.html", users=users)
    else:
        return jsonify({"error": "Database connection error"}), 500


# Web Interface: Add user
@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    if request.method == "GET":
        return render_template("add_user.html")
    elif request.method == "POST":
        data = request.form
        phone_number = data.get("phone_number")
        name = data.get("name")
        access = bool(data.get("access"))

        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO authorized_users (phone_number, name, access) VALUES (%s, %s, %s)",
                (phone_number, name, access),
            )
            conn.commit()
            cur.close()
            conn.close()
            return redirect("/web")
        else:
            return jsonify({"error": "Database connection error"}), 500


# Web Interface: Edit user
@app.route("/edit_user/<int:user_id>", methods=["GET", "POST"])
def edit_user(user_id):
    conn = get_db_connection()
    if request.method == "GET":
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT phone_number, name, access FROM authorized_users WHERE id = %s", (user_id,))
            user = cur.fetchone()
            cur.close()
            conn.close()
            return render_template("edit_user.html", user=user, user_id=user_id)
    elif request.method == "POST":
        data = request.form
        phone_number = data.get("phone_number")
        name = data.get("name")
        access = bool(data.get("access"))

        if conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE authorized_users SET phone_number = %s, name = %s, access = %s WHERE id = %s",
                (phone_number, name, access, user_id),
            )
            conn.commit()
            cur.close()
            conn.close()
            return redirect("/web")
    return jsonify({"error": "Database connection error"}), 500


# Web Interface: Delete user
@app.route("/delete_user/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM authorized_users WHERE id = %s", (user_id,))
        conn.commit()
        cur.close()
        conn.close()
        return redirect("/web")
    return jsonify({"error": "Database connection error"}), 500


if __name__ == "__main__":
    app.run(debug=True)
