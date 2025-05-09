from flask import Blueprint, request, render_template, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from decimal import Decimal
from models.db import get_cursor

# Create profile blueprint
profile_bp = Blueprint('profile', __name__)

@profile_bp.route("/profile")
def profile():
    # Geting all the data of the logged in user
    cur, db = get_cursor()
    cur.execute("SELECT * FROM users WHERE user_id = %s", (int(session.get("user_id")), ))
    user_tuple = cur.fetchall()[0]
    cur.close()
    db.close()

    if user_tuple[4] == "A":
        user_type = "Admin"
    elif user_tuple[4] == "R":
        user_type = "Researcher"
    else:
        user_type = "Viewer"

    user = {
        "user_name" : user_tuple[1],
        "email" : user_tuple[2],
        "user_type" : user_type,
        "latitude" : user_tuple[5],
        "longitude" : user_tuple[6],
        "first_name" : user_tuple[7],
        "last_name" : user_tuple[8]
    }

    return render_template("profile.html", user=user)


@profile_bp.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():
    if request.method == "GET":
        return render_template("edit_profile.html")

    if request.method == "POST":
        email = request.form.get("email")
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")

        # Gets the user data form the database and replace the none with them
        cur, db = get_cursor()
        cur.execute("SELECT * FROM users WHERE user_id = %s", (session.get("user_id"), ))
        user_data_old = cur.fetchall()[0]
        cur.close()
        db.close()

        user_data_new = {}

        if not email:
            user_data_new["email"] = user_data_old[2]
        else:
            # Cheks if email exists or not
            cur, db = get_cursor()
            cur.execute("SELECT * FROM users WHERE email = %s", (email, ))
            if cur.rowcount > 0:
                session["error_massage"] = "Email is allready assined to another user please try again"
                return redirect("/apology")
            user_data_new["email"] = email

        
        # Checks latitude and longitude 
        if not latitude:
            user_data_new["latitude"] = user_data_old[5]
        else:
            if not (-90 <= float(latitude) <= 90):
                session["error_massage"] = "latitude must be between (-90) and (90)"
                return redirect("/apology")
            else:
                user_data_new["latitude"] = latitude
       
        if not longitude:
            user_data_new["longitude"] = user_data_old[6]
        else:
            if not (-180 <= float(longitude) <= 180):
                session["error_massage"] = "longitude must be between (-180) and (180)"
                return redirect("/apology")
            else:
                user_data_new["longitude"] = longitude


        if not first_name:
            user_data_new["first_name"] = user_data_old[7]
        else:
             user_data_new["first_name"] = first_name
        
        if not last_name:
            user_data_new["last_name"] = user_data_old[8]
        else:
             user_data_new["last_name"] = last_name
        
        # Updating database with the new data (Using old data if new data is not provited by the user)
        cur, db = get_cursor()
        query = "UPDATE users SET email = %s, latitude = %s, longitude = %s, first_name = %s, last_name = %s WHERE user_id = %s"
        data = (user_data_new["email"], user_data_new["latitude"], user_data_new["longitude"], user_data_new["first_name"], user_data_new["last_name"], session.get("user_id"))
        cur.execute(query, data)
        db.commit()
        cur.close()
        db.close()
        
        return redirect(url_for("profile.profile"))


@profile_bp.route("/change_password", methods=["GET", "POST"])
def change_password():
    if request.method == "GET":
        return render_template("change_password.html")
    
    if request.method == "POST":
        old_password = request.form.get("password_old")
        password = request.form.get("password")
        password_again = request.form.get("password_again")

        if not password or not password_again and not old_password:
            session["error_massage"] = "Please fill all the filds"
            return redirect("/apology")
        
        if password != password_again:
            session["error_massage"] = "Confirmation password does not match"
            return redirect("/apology")
        
        cur, db = get_cursor()
        cur.execute("SELECT password_hash FROM users WHERE user_id = %s", (session.get("user_id"), ))
        
        # Checking if the privious password is correct
        if check_password_hash(cur.fetchall()[0][0], old_password):
            cur.close()
            db.close()
            cur, db = get_cursor()
            cur.execute("UPDATE users SET password_hash = %s WHERE user_id = %s", (
                str(generate_password_hash(password)),
                session.get("user_id")
            ))
            db.commit()
            cur.close()
            db.close()

        else:
            session["error_massage"] = "Incorrect Password, please try again"
            return redirect("/apology")

        return redirect(url_for("profile.profile")) 