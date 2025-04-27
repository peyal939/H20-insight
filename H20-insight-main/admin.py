from werkzeug.security import  generate_password_hash

import getpass

import mysql.connector 

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="4044",
    database="water"
)


while True:
    user_name = input("Username: ")
    email = input("Email: ")

    if not user_name or not email:
        print("Please fill all the required filds")
        continue

    cur = db.cursor(buffered=True)
    cur.execute("SELECT * FROM users WHERE user_name = %s OR email = %s", (user_name, email))

    if cur.rowcount > 0:
        print("Usarname taken or email email allraedy in use")
        cur.close()
        continue

    break 

while True:
    password = getpass.getpass("Password: ")
    password_again = getpass.getpass("Password (again): ")

    if password == password_again:
        break

    elif not password or not password_again:
        print("Please fill all the required filds")
    
    else:
        print("Confirmation password does not match, pls try again")

cur = db.cursor()

query = "INSERT INTO users (user_name, email, password_hash, user_type) VALUES (%s, %s, %s, %s)"
data = (user_name, email, str(generate_password_hash(password)), "A")
cur.execute(query, data)
db.commit()
cur.close()
print("Admind/Superuser created successfully")
