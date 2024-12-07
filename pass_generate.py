from werkzeug.security import generate_password_hash

hashed_password = generate_password_hash("MAN@13diesel")
print(hashed_password)