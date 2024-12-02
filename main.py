from flask import Flask, jsonify, request
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# Get the database URL from the environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

# Function to connect to the database
def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require', cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None

@app.route("/")
def index():
    return jsonify({"message": "Welcome to the Gate Management System API!"})

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

if __name__ == "__main__":
    app.run(debug=True)
