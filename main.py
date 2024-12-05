from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure random key

# Database connection setup
DATABASE_URL = 'your_postgresql_database_url'

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# Route for login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, password FROM admin_users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid username or password.")
    return render_template('login.html')

# Route for logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

# Protected route decorator
def login_required(func):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# Index route (protected)
@app.route('/')
@login_required
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, phone_number, name, access FROM users")
    users = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', users=users)

# Other routes (add_user, edit_user, delete_user) - Add @login_required to each route
@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if request.method == 'POST':
        phone_number = request.form['phone_number']
        name = request.form['name']
        access = 'access' in request.form

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (phone_number, name, access) VALUES (%s, %s, %s)",
                    (phone_number, name, access))
        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for('index'))
    return render_template('add_user.html')

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        phone_number = request.form['phone_number']
        name = request.form['name']
        access = 'access' in request.form

        cur.execute("UPDATE users SET phone_number = %s, name = %s, access = %s WHERE id = %s",
                    (phone_number, name, access, user_id))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('index'))

    cur.execute("SELECT phone_number, name, access FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    return render_template('edit_user.html', user=user, user_id=user_id)

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
