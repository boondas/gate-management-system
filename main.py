from flask import Flask, jsonify
import os
import psycopg2

app = Flask(__name__)

def connect_to_database():
    # Fetch the DATABASE_URL environment variable
    DATABASE_URL = os.getenv(postgres://uf8dggiba24i76:p9c124a134a00bf372ab46ca587a95af4e21473d2dbea5657c9a2b228abbe5bce@c3nv2ev86aje4j.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/de18ue68rrh2g1)
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is not set.")
    
    # Connect to the database
    return psycopg2.connect(DATABASE_URL, sslmode='require')

@app.route("/")
def home():
    try:
        # Establish connection to the database
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("SELECT 'Database connection successful!'")
        message = cursor.fetchone()
        return jsonify({"message": message[0]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
