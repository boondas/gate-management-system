from werkzeug.security import generate_password_hash

# Replace 'your_password' with your desired admin password
password = 'Man@13diesel'
hashed_password = generate_password_hash(password)
print(f"Hashed Password: {hashed_password}")