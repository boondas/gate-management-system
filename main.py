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

# Add User
@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        phone_number = request.form.get('phone_number')
        name = request.form.get('name')
        access = request.form.get('access') == 'on'

        if not phone_number or not name:
            return "Phone number and name are required!", 400

        try:
            conn = connect_to_database()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (phone_number, name, access) VALUES (%s, %s, %s) "
                "ON CONFLICT (phone_number) DO UPDATE SET name = EXCLUDED.name, access = EXCLUDED.access",
                (phone_number, name, access)
            )
            conn.commit()
            conn.close()
            return redirect(url_for('home'))
        except Exception as e:
            return f"Error adding user: {str(e)}", 500
    return render_template('add_user.html')

# Edit User
@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    try:
        conn = connect_to_database()
        cursor = conn.cursor()

        if request.method == 'POST':
            phone_number = request.form.get('phone_number')
            name = request.form.get('name')
            access = request.form.get('access') == 'on'

            cursor.execute(
                "UPDATE users SET phone_number = %s, name = %s, access = %s WHERE id = %s",
                (phone_number, name, access, user_id)
            )
            conn.commit()
            conn.close()
            return redirect(url_for('home'))

        cursor.execute("SELECT phone_number, name, access FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        conn.close()
        return render_template('edit_user.html', user_id=user_id, user=user)
    except Exception as e:
        return f"Error editing user: {str(e)}", 500

# Delete User
@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        conn.close()
        return redirect(url_for('home'))
    except Exception as e:
        return f"Error deleting user: {str(e)}", 500

# Validate User
@app.route('/validate_user', methods=['GET'])
def validate_user():
    phone_number = request.args.get('phone_number')
    if not phone_number:
        return jsonify({"status": "ERROR", "message": "Phone number is required"}), 400

    phone_number = re.sub(r'\D', '', phone_number)

    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("SELECT name, access FROM users WHERE REPLACE(phone_number, '+', '') = %s", (phone_number,))
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
