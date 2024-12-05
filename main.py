import os
from urllib.parse import urlparse
from dotenv import load_dotenv  # To load environment variables
import psycopg2
from flask import Flask, request, jsonify, render_template, redirect, url_for, send_from_directory

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Database Connection
def connect_to_database():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise Exception("DATABASE_URL is not set in environment variables.")

    # Parse DATABASE_URL to extract connection components
    url = urlparse(database_url)
    return psycopg2.connect(
        host=url.hostname,
        database=url.path[1:],  # Remove leading slash from the database name
        user=url.username,
        password=url.password,
        port=url.port
    )

# Validation API for ESP32
@app.route('/validate_user', methods=['GET'])
def validate_user():
    phone_number = request.args.get('phone_number')
    print(f"Received Phone Number: {phone_number}")  # Debugging log

    if not phone_number:
        return jsonify({"status": "ERROR", "message": "Phone number is required"}), 400

    # Normalize the phone number
    if phone_number.startswith("0"):
        phone_number = "+27" + phone_number[1:]
    print(f"Normalized Phone Number: {phone_number}")  # Debugging log

    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("SELECT name, access FROM users WHERE phone_number = %s", (phone_number,))
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

# Other routes omitted for brevity

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
