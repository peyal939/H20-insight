import sqlite3
from werkzeug.security import generate_password_hash
import getpass
from config import DB_CONFIG

# Connect to SQLite database
db = sqlite3.connect(DB_CONFIG["database"])
db.execute("PRAGMA foreign_keys = ON")

while True:
    user_name = input("Username: ")
    email = input("Email: ")

    if not user_name or not email:
        print("Please fill all the required fields")
        continue

    cur = db.cursor()
    cur.execute("SELECT * FROM users WHERE user_name = ? OR email = ?", (user_name, email))

    # SQLite doesn't have rowcount, check if there are rows
    if cur.fetchone():
        print("Username taken or email already in use")
        cur.close()
        continue

    break 

while True:
    password = getpass.getpass("Password: ")
    password_again = getpass.getpass("Password (again): ")

    if password == password_again:
        break

    elif not password or not password_again:
        print("Please fill all the required fields")
    
    else:
        print("Confirmation password does not match, please try again")

cur = db.cursor()

query = "INSERT INTO users (user_name, email, password_hash, user_type) VALUES (?, ?, ?, ?)"
data = (user_name, email, str(generate_password_hash(password)), "A")
cur.execute(query, data)
db.commit()
cur.close()
db.close()
print("Admin/Superuser created successfully")
