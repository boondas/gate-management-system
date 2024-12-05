import os
import re
from urllib.parse import urlparse
from dotenv import load_dotenv
import psycopg2
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from werkzeug.security import check_password_hash

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your_secret_key")  # Add a secure secret key in your .env file

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

# Authentication Middleware
def login_required(func):
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            flash("You need to log in to access this page.", "danger")
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            conn = connect_to_database()
            cursor = conn.cursor()
            cursor.execute("SELECT password FROM admin_users WHERE username = %s", (username,))
            user = cursor.fetchone()
            conn.close()

            if user and check_password_hash(user[0], password):
                session['username'] = username
                flash("Login successful!", "success")
                return redirect(url_for('home'))
            else:
                flash("Invalid username or password.", "danger")
        except Exception as e:
            return f"Error logging in: {str(e)}", 500

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("You have been logged out.", "success")
    return redirect(url_for('login'))

@app.route('/')
@login_required
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

# Other routes (add_user, edit_user, delete_user, validate_user)
# Add the `@login_required` decorator to protect these routes.

@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    # Your existing code for add_user

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    # Your existing code for edit_user

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    # Your existing code for delete_user

@app.route('/validate_user', methods=['GET'])
def validate_user():
    # This route doesn't require authentication
    # Your existing code for validate_user

# Serve Static Files
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
