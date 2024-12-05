import os
from urllib.parse import urlparse
from dotenv import load_dotenv  # To load environment variables
import psycopg2
from flask import Flask, request, jsonify, render_template, redirect, url_for, send_from_directory
import phonenumbers  # Import phonenumbers library to handle phone numbers

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Define the country code (e.g., +27 for South Africa)
COUNTRY_CODE = "+27"

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

# Normalize the phone number to ensure it has the country code
def normalize_phone_number(phone_number):
    try:
        # Check if phone number already has the country code
        if phone_number.startswith(COUNTRY_CODE):
            return phone_number
        # Otherwise, add the country code
        else:
            return COUNTRY_CODE + phone_number
    except Exception as e:
        return None

@app.route('/validate_user', methods=['GET'])
def validate_user():
    phone_number = request.args.get('phone_number')
    if not phone_number:
        return jsonify({"status": "ERROR", "message": "Phone number is required"}), 400

    # Normalize phone number
    normalized_number = normalize_phone_number(phone_number)
    if not normalized_number:
        return jsonify({"status": "ERROR", "message": "Invalid phone number format"}), 400

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

# Serve Static Files
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
