import psycopg2
from flask import Flask, request, jsonify, render_template, redirect, url_for
import serial
import serial.tools.list_ports
import threading
import time

app = Flask(__name__)
arduino = None  # Placeholder for the Arduino serial connection


# Arduino Initialization
def initialize_arduino_connection():
    global arduino
    try:
        ports = serial.tools.list_ports.comports()
        available_ports = [port.device for port in ports]
        print(f"Available ports: {available_ports}")
        arduino = serial.Serial(port='COM6', baudrate=9600, timeout=1)
        print("Arduino connected successfully!")
    except serial.SerialException as e:
        print(f"Error initializing Arduino: {e}")
        arduino = None


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


# Arduino Communication Thread
def arduino_communication():
    if arduino is None:
        print("Arduino is not connected. Aborting communication.")
        return

    print("Starting Arduino communication...")
    while True:
        try:
            if arduino.in_waiting > 0:
                raw_data = arduino.readline().decode(errors='ignore').strip()
                print(f"Raw data received: {raw_data}")

                phone_number = raw_data
                print(f"Phone number received: {phone_number}")

                conn = connect_to_database()
                cursor = conn.cursor()
                cursor.execute("SELECT name, access FROM users WHERE phone_number = %s", (phone_number,))
                result = cursor.fetchone()
                conn.close()

                if result:
                    name, access = result
                    if access:
                        print(f"Authorized! User: {name} ({phone_number}).")
                        arduino.write(b"VALID\n")
                    else:
                        print(f"Access denied for {name} ({phone_number}).")
                        arduino.write(b"DENIED\n")
                else:
                    print(f"Unauthorized number: {phone_number}.")
                    arduino.write(b"INVALID\n")
        except Exception as e:
            print(f"Error during communication: {e}")
        time.sleep(0.1)


# Flask Web Interface in a Thread
def run_web_interface():
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    initialize_arduino_connection()

    if arduino is not None:
        arduino_thread = threading.Thread(target=arduino_communication, daemon=True)
        arduino_thread.start()

    run_web_interface()
