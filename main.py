import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secure session cookies

# Database connection setup
def get_db_connection():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    return conn

# Login required decorator to protect admin routes
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Route for the home page (Dashboard)
@app.route('/')
@login_required
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM admin_users")
    users = cur.fetchall()
    conn.close()
    return render_template('index.html', users=users)

# Route for adding a user
@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO admin_users (username, password) VALUES (%s, %s)", (username, hashed_password))
        conn.commit()
        conn.close()

        flash('User added successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('add_user.html')

# Route for editing user details
@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        cur.execute("UPDATE admin_users SET username = %s, password = %s WHERE id = %s", (username, hashed_password, user_id))
        conn.commit()
        conn.close()

        flash('User details updated successfully!', 'success')
        return redirect(url_for('index'))

    cur.execute("SELECT * FROM admin_users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    conn.close()

    return render_template('edit_user.html', user=user)

# Route for deleting a user
@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM admin_users WHERE id = %s", (user_id,))
    conn.commit()
    conn.close()

    flash('User deleted successfully!', 'success')
    return redirect(url_for('index'))

# Route for login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM admin_users WHERE username = %s", (username,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):  # user[1] contains the hashed password
            session['admin_logged_in'] = True
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')

    return render_template('login.html')

# Route for logout
@app.route('/logout')
@login_required
def logout():
    session.pop('admin_logged_in', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
