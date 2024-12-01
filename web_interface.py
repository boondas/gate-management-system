from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Connect to the database
def connect_to_database():
    return sqlite3.connect("users.db")

@app.route('/')
def home():
    return '''
    <h1>Welcome to the Gate Management System</h1>
    <p>Use the following endpoints:</p>
    <ul>
        <li><b>POST /add</b>: Add a phone number (JSON: {"phone_number": "+1234567890"}).</li>
        <li><b>POST /remove</b>: Remove a phone number (JSON: {"phone_number": "+1234567890"}).</li>
        <li><b>GET /list</b>: List all authorized phone numbers.</li>
    </ul>
    '''

@app.route('/add', methods=['POST'])
def add_user():
    phone_number = request.json.get('phone_number')
    conn = connect_to_database()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (phone_number) VALUES (?)", (phone_number,))
    conn.commit()
    conn.close()
    return jsonify({"message": f"Phone number {phone_number} added."})

@app.route('/remove', methods=['POST'])
def remove_user():
    phone_number = request.json.get('phone_number')
    conn = connect_to_database()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE phone_number = ?", (phone_number,))
    conn.commit()
    conn.close()
    return jsonify({"message": f"Phone number {phone_number} removed."})

@app.route('/list', methods=['GET'])
def list_users():
    conn = connect_to_database()
    cursor = conn.cursor()
    cursor.execute("SELECT phone_number FROM users")
    users = cursor.fetchall()
    conn.close()
    return jsonify({"users": [user[0] for user in users]})

@app.route('/favicon.ico')
def favicon():
    return '', 204

if __name__ == '__main__':
    app.run(debug=True, port=5000)
