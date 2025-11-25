import os
import re
from urllib.parse import urlparse
from dotenv import load_dotenv
import psycopg2
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import timedelta, datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Secret key
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")

# Session lifetime
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)


# ---------------------------
#  DATABASE CONNECTION
# ---------------------------
def connect_to_database():
    try:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL not found in .env")

        url = urlparse(database_url)

        conn = psycopg2.connect(
            host=url.hostname,
            database=url.path[1:],
            user=url.username,
            password=url.password,
            port=url.port,
            sslmode="require" if "sslmode=require" in database_url else None
        )

        return conn

    except Exception as e:
        print(f"Database connection error: {e}")
        raise


# ---------------------------
#   LOGIN REQUIRED DECORATOR
# ---------------------------
def login_required(func):
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            flash("You must log in first.", "danger")
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


# ---------------------------
#   SESSION TIMEOUT CHECK
# ---------------------------
@app.before_request
def check_session_timeout():
    if 'user' in session:
        last_activity = session.get('last_activity')
        now = datetime.now()

        if last_activity:
            last_time = datetime.strptime(last_activity, "%Y-%m-%d %H:%M:%S")
            if now - last_time > app.config['PERMANENT_SESSION_LIFETIME']:
                session.clear()
                flash("Session expired. Please log in again.", "danger")
                return redirect(url_for('login'))

        session['last_activity'] = now.strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------
#   LOGIN ROUTE
# ---------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        try:
            conn = connect_to_database()
            cur = conn.cursor()
            cur.execute("SELECT password FROM admin_users WHERE username = %s", (username,))
            result = cur.fetchone()
            conn.close()

            if result and check_password_hash(result[0], password):
                session["user"] = username
                session["last_activity"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return redirect(url_for("home"))
            else:
                flash("Invalid credentials.", "danger")

        except Exception as e:
            flash(f"Login error: {e}", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------------------
#   HOME ROUTE
# ---------------------------
@app.route("/")
@login_required
def home():
    try:
        conn = connect_to_database()
        cur = conn.cursor()
        cur.execute("SELECT id, phone_number, name, access FROM users ORDER BY id ASC")
        users = cur.fetchall()
        conn.close()

        return render_template("index.html", users=users)

    except Exception as e:
        flash(f"Error loading users: {e}", "danger")
        return redirect(url_for("login"))


# ---------------------------
#   DASHBOARD ROUTE
# ---------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    try:
        conn = connect_to_database()
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM users")
        total_users = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM users WHERE access = TRUE")
        allowed = cur.fetchone()[0]
        denied = total_users - allowed

        cur.execute("SELECT name, phone_number, access FROM users ORDER BY id DESC LIMIT 5")
        recent = cur.fetchall()

        conn.close()

        return render_template(
            "dashboard.html",
            total_users=total_users,
            access_granted=allowed,
            access_denied=denied,
            recent_activity=recent
        )

    except Exception as e:
        flash(f"Dashboard error: {e}", "danger")
        return redirect(url_for("home"))


# ---------------------------
#   ADD USER
# ---------------------------
@app.route("/add_user", methods=["GET", "POST"])
@login_required
def add_user():
    if request.method == "POST":
        phone = request.form.get("phone_number")
        name = request.form.get("name")
        access = request.form.get("access") == "on"

        try:
            conn = connect_to_database()
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO users (phone_number, name, access)
                VALUES (%s, %s, %s)
            """, (phone, name, access))

            conn.commit()
            conn.close()

            flash("User added!", "success")
            return redirect(url_for("home"))

        except Exception as e:
            flash(f"Error adding user: {e}", "danger")

    return render_template("add_user.html")


# ---------------------------
#   EDIT USER
# ---------------------------
@app.route("/edit_user/<int:user_id>", methods=["GET", "POST"])
@login_required
def edit_user(user_id):
    try:
        conn = connect_to_database()
        cur = conn.cursor()

        if request.method == "POST":
            phone = request.form.get("phone_number")
            name = request.form.get("name")
            access = request.form.get("access") == "on"

            cur.execute("""
                UPDATE users
                SET phone_number=%s, name=%s, access=%s
                WHERE id=%s
            """, (phone, name, access, user_id))

            conn.commit()
            conn.close()

            flash("User updated!", "success")
            return redirect(url_for("home"))

        cur.execute("SELECT phone_number, name, access FROM users WHERE id=%s", (user_id,))
        user = cur.fetchone()
        conn.close()

        return render_template("edit_user.html", user_id=user_id, user=user)

    except Exception as e:
        flash(f"Error editing: {e}", "danger")
        return redirect(url_for("home"))


# ---------------------------
#   DELETE USER
# ---------------------------
@app.route("/delete_user/<int:user_id>", methods=["POST"])
@login_required
def delete_user(user_id):
    try:
        conn = connect_to_database()
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
        conn.commit()
        conn.close()

        flash("User deleted!", "success")
        return redirect(url_for("home"))

    except Exception as e:
        flash(f"Delete error: {e}", "danger")
        return redirect(url_for("home"))


# ---------------------------
#   VALIDATE USER (ESP32)
# ---------------------------
@app.route("/validate_user")
def validate_user():
    phone = request.args.get("phone_number")
    if not phone:
        return jsonify({"status": "ERROR", "message": "Phone number missing"}), 400

    phone = re.sub(r"\D", "", phone)

    try:
        conn = connect_to_database()
        cur = conn.cursor()

        cur.execute("""
            SELECT name, access FROM users
            WHERE REPLACE(phone_number, '+', '') = %s
        """, (phone,))

        result = cur.fetchone()
        conn.close()

        if not result:
            return jsonify({"status": "INVALID"}), 404

        name, access = result
        if access:
            return jsonify({"status": "VALID", "message": f"Access granted for {name}"})
        else:
            return jsonify({"status": "DENIED"})

    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500

# ---------------------------
#   HEALTH CHECK ROUTE
# ---------------------------
@app.route("/health")
def health():
    return jsonify({"status": "OK"}), 200


# ---------------------------
# CREATE DEFAULT ADMIN
# ---------------------------
def create_default_admin():
    try:
        conn = connect_to_database()
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM admin_users")
        count = cur.fetchone()[0]

        if count == 0:
            pwd = generate_password_hash("Admin123!")
            cur.execute("INSERT INTO admin_users (username, password) VALUES (%s, %s)",
                        ("admin", pwd))
            conn.commit()
            print("Default admin created.")

        conn.close()

    except Exception as e:
        print(f"Admin creation error: {e}")


# Run admin creation
create_default_admin()


# ---------------------------
# START FLASK
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)
