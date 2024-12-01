import sqlite3
import serial

# XOR encryption key (must match Arduino's key)
XOR_KEY = 'K'  # Ensure this matches the Arduino code

# XOR function to encrypt/decrypt
def xor_encrypt_decrypt(input_string):
    return ''.join(chr(ord(char) ^ ord(XOR_KEY)) for char in input_string)

# Connect to the database
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Set up Serial communication
arduino = serial.Serial(port='COM6', baudrate=9600, timeout=1)  # Adjust COM port as needed
print("Python script ready and listening...")

while True:
    if arduino.in_waiting > 0:
        # Read encrypted phone number from Arduino
        encrypted_phone_number = arduino.readline().decode().strip()
        phone_number = xor_encrypt_decrypt(encrypted_phone_number)  # Decrypt it
        print(f"Received (decrypted): {phone_number}")

        # Check if the phone number exists in the database
        cursor.execute("SELECT * FROM users WHERE phone_number = ?", (phone_number,))
        result = cursor.fetchone()

        # Prepare encrypted response
        if result:
            response = "VALID"
            print("Authorized number!")
        else:
            response = "INVALID"
            print("Unauthorized number!")

        encrypted_response = xor_encrypt_decrypt(response)  # Encrypt response
        arduino.write((encrypted_response + "\n").encode())  # Send it back
