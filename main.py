import os
import re
from urllib.parse import urlparse
from dotenv import load_dotenv
import psycopg2
from flask import Flask, request, jsonify, render_template, redirect, url_for, send_from_directory

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Database Connection
def connect_to_database():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise Exception("DATABASE_URL is not set in environment variables.")

    url = urlparse(database_url)
    return psycopg2.connect(
        host=url.hostname,
        database=url.path[1:],  # Remove leading slash
        user=url.username,
        password=url.password,
        port=url.port
    )

# Normalize Phone Number
def normalize_phone_number(phone_number):
    # Remove all non-numeric characters except '+'
    phone_number = re.sub(r'[^\d+]', '', phone_number)

    # Convert to international format if needed (assumes South Africa: +27)
    if phone_number.startswith('0'):  # Local format (071...)
        phone_number = '+27' + phone_number[1:]
    elif not phone_number.startswith('+'):  # No '+' prefix (27...)
        phone_number = '+' + phone_number
    return phone_number

# Home Route
@app.route('/')
def home():
    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("SELECT id, phone_number, name, access FROM users")
        users = cursor.fetchall()
        conn.close()
        return render_template('index.html', users=users)
    except Exception as e:
        return f"Error fetching users: {str(e)}", 500

# Validation API for ESP32
@app.route('/validate_user', methods=['GET'])
def validate_user():
    phone_number = request.args.get('phone_number')
    if not phone_number:
        return jsonify({"status": "ERROR", "message": "Phone number is required"}), 400

    # Normalize the phone number
    normalized_number = normalize_phone_number(phone_number)

    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("SELECT name, access FROM users WHERE phone_number = %s", (normalized_number,))
        result = cursor.fetchone()
        conn.close()

        if result:
            name, access = result
            if access:
                return jsonify({"status": "VALID", "message": f"Access granted for {name}"})
            else:
                return jsonify({"status": "DENIED", "message": "Access denied"})
        else:
            return jsonify({"status": "INVALID", "message": "Unauthorized phone number"})
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
