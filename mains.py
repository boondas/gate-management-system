from flask import Flask, request, jsonify, render_template, redirect, url_for
import psycopg2

app = Flask(__name__)

# Database Connection
def connect_to_database():
    return psycopg2.connect(
        host="localhost",
        database="gate_management",
        user="postgres",
        password="MAN@13diesel"
    )

# Home Route
@app.route('/')
def home():
    conn = connect_to_database()
    cursor = conn.cursor()
    cursor.execute("SELECT id, phone_number, name, access FROM users")
    users = cursor.fetchall()
    conn.close()
    return render_template('index.html', users=users)

# Add User Route
@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        phone_number = request.form.get('phone_number')
        name = request.form.get('name')
        access = request.form.get('access') == 'on'

        if not phone_number or not name:
            return "Phone number and name are required!", 400

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
    return render_template('add_user.html')

# Edit User Route
@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
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

# Delete User Route
@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    conn = connect_to_database()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('home'))

# Validation API for ESP32
@app.route('/validate_user', methods=['GET'])
def validate_user():
    phone_number = request.args.get('phone_number')
    if not phone_number:
        return jsonify({"status": "ERROR", "message": "Phone number is required"}), 400

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

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)