from flask import Blueprint, request, render_template, session, redirect, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from models.db import get_cursor

# Create auth blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    
    if request.method == "POST":
        email = request.form.get("email")
        user_name = request.form.get("username")
        password = request.form.get("password")
        password_again = request.form.get("password_again")
        user_type = request.form.get("user_type")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")

        if user_type not in ["V", "R"]:
            session["error_massage"] = "Invalid user type."
            return redirect("/apology")

        if not password or not password_again or not user_name or not email or not user_type:
            session["error_massage"] = "Please fill out all the required fields."
            return redirect("/apology")

        if password != password_again:
            session["error_massage"] = "Confirmation password doesn't match."
            return redirect("/apology")
        
        if not first_name or not last_name:
            session["error_massage"] = "Please provide first name and last name."
            return redirect("/apology")
        
        # Check if username is taken or email is already in use
        cur, db = get_cursor()

        query = "SELECT * FROM users WHERE user_name = ? or email = ?"
        data = (user_name, email)
        cur.execute(query, data)
        
        if cur.fetchone():
            cur.close()
            db.close()
            session["error_massage"] = "Username taken or email allready in use"
            return redirect("/apology")

        cur.close()
        db.close()

        cur, db = get_cursor()

        query = "INSERT INTO users (user_name, email, password_hash, user_type, latitude, longitude, first_name, last_name) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        data = (user_name, email, str(generate_password_hash(password)), user_type, 0.0, 0.0, first_name, last_name)
        cur.execute(query, data)
        
        db.commit()
        cur.close()
        db.close()

        return redirect("/login")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect("/")

    if request.method == "GET":
        return render_template("login.html")
    
    if request.method == "POST":
        identification = request.form.get("identification")
        password = request.form.get("password")

        if not identification:
            session["error_massage"] = "Must provide username or email"
            return redirect("/apology")

        if not password:
            session["error_massage"] = "Must provide password"
            return redirect("/apology")

        cur, db = get_cursor()

        query = "SELECT * FROM users WHERE user_name = ? OR email = ?"
        data = (identification, identification)
        cur.execute(query, data)
        
        user = cur.fetchone()
        if not user:
            session["error_massage"] = "Invalid username or email"
            return redirect("/apology")
        
        # Re-execute to get all columns since we consumed the result
        cur.execute(query, data)
        user = cur.fetchall()[0]

        #  user[3] = password_hash
        if check_password_hash(user[3], password):
            session["user_id"] = user[0]
            session["user_name"] = user[1]
            session["user_type"] = user[4]

        else:
            session["error_massage"] = "incorrect password"
            return redirect("/apology")
    
        cur.close()
        db.close()
        return redirect("/")
        
        
@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@auth_bp.route("/apology")
def apology():
    error_massage = session.get("error_massage", "Unknown error")
    session["error_massage"] = None
    return render_template("apology.html", error_massage=error_massage) 