from werkzeug.security import generate_password_hash

# Replace this with your desired password
password = "your_admin_password"

# Generate the hashed password
hashed_password = generate_password_hash(password)
print("Hashed Password:", hashed_password)
