import os
import re
from urllib.parse import urlparse
from dotenv import load_dotenv
import psycopg2
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from datetime import timedelta, datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Secret key for sessions
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")

# Configure session lifetime
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)

@app.before_request
def check_session_timeout():
    if 'user' in session:
        last_activity = session.get('last_activity')
        current_time = datetime.now()

        if last_activity:
            last_activity_time = datetime.strptime(last_activity, "%Y-%m-%d %H:%M:%S")
            if current_time - last_activity_time > app.config['PERMANENT_SESSION_LIFETIME']:
                session.clear()
                flash("Session timed out. Please log in again.", "danger")
                return redirect(url_for('login'))

        session['last_activity'] = current_time.strftime("%Y-%m-%d %H:%M:%S")

# Database Connection Function
def connect_to_database():
    try:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL is not set in environment variables.")

        url = urlparse(database_url)
        conn = psycopg2.connect(
            host=url.hostname,
            database=url.path[1:],  # Remove leading slash
            user=url.username,
            password=url.password,
            port=url.port
        )
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        raise

# Authentication Middleware
def login_required(func):
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            flash("You need to log in to access this page.", "danger")
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            conn = connect_to_database()
            cursor = conn.cursor()
            cursor.execute("SELECT password FROM admin_users WHERE username = %s", (username,))
            result = cursor.fetchone()
            conn.close()

            if result and check_password_hash(result[0], password):
                session['user'] = username
                session['last_activity'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return redirect(url_for('home'))
            else:
                flash("Invalid credentials, please try again.", "danger")
        except Exception as e:
            flash(f"An error occurred during login: {e}", "danger")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():
    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("SELECT phone_number, name, access FROM users ORDER BY id ASC")  # Fetch all users
        users = cursor.fetchall()
        conn.close()

        # Add a sequential ID for display
        users_with_index = [(index + 1, *user) for index, user in enumerate(users)]

        return render_template('index.html', users=users_with_index)
    except Exception as e:
        flash(f"Error fetching users: {e}", "danger")
        return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE access = TRUE")
        access_granted = cursor.fetchone()[0]
        access_denied = total_users - access_granted

        cursor.execute("SELECT name, phone_number, access FROM users ORDER BY id DESC LIMIT 5")
        recent_activity = cursor.fetchall()
        conn.close()

        return render_template(
            'dashboard.html',
            total_users=total_users,
            access_granted=access_granted,
            access_denied=access_denied,
            recent_activity=recent_activity
        )
    except Exception as e:
        flash(f"Error loading dashboard: {e}", "danger")
        return redirect(url_for('home'))

@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if request.method == 'POST':
        phone_number = request.form.get('phone_number')
        name = request.form.get('name')
        access = request.form.get('access') == 'on'

        if not phone_number or not name:
            flash("Phone number and name are required!", "danger")
            return redirect(url_for('add_user'))

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
            flash("User added successfully!", "success")
            return redirect(url_for('home'))
        except Exception as e:
            flash(f"Error adding user: {e}", "danger")

    return render_template('add_user.html')

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
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
            flash("User updated successfully!", "success")
            return redirect(url_for('home'))

        cursor.execute("SELECT phone_number, name, access FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        conn.close()
        return render_template('edit_user.html', user_id=user_id, user=user)
    except Exception as e:
        flash(f"Error editing user: {e}", "danger")
        return redirect(url_for('home'))

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        conn.close()
        flash("User deleted successfully!", "success")
        return redirect(url_for('home'))
    except Exception as e:
        flash(f"Error deleting user: {e}", "danger")
        return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
