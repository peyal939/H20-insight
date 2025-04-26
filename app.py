from flask import Flask, request, render_template,session, redirect, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from flask_session import Session

from decimal import Decimal

import random

# Database setup
import mysql.connector 

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="4044",
    database="water"
)

# App config
app = Flask(__name__)

# Session config 
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# landing page and search
@app.route("/" , methods=["GET", "POST"])
def index():
    if request.method == "GET":
        if session.get("user_id"):      
            return render_template("index.html")
        
        else:
            return redirect("/login")
        
    if request.method == "POST":
        q = request.form.get("q")

        cur = db.cursor(buffered=True)
        query = "SELECT * FROM locations WHERE location_name LIKE %s"
        data = ("%" + str(q) + "%", )
        cur.execute(query, data) 
        search_result = cur.fetchall()

        cur.close()

        return render_template("search.html", search_result=search_result, q=str(q))


@app.route("/register", methods=["GET", "POST"])
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
        cur = db.cursor(buffered=True)

        query = "SELECT * FROM users WHERE user_name = %s or email = %s"
        data = (user_name, email)
        cur.execute(query, data)
        
        if cur.rowcount > 0:
            cur.close()
            session["error_massage"] = "Username taken or email allready in use"
            return redirect("/apology")

        cur.close()

        cur = db.cursor(buffered=True)

        query = "INSERT INTO users (user_name, email, password_hash, user_type, latitude, longitude, first_name, last_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        data = (user_name, email, str(generate_password_hash(password)), user_type, Decimal("0.0"), Decimal("0.0"), first_name, last_name)
        cur.execute(query, data)
        
        db.commit()
        cur.close()

        return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect("index")

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

        cur = db.cursor(buffered=True)

        query = "SELECT * FROM users WHERE user_name = %s OR email = %s"
        data = (identification, identification)
        cur.execute(query, data)
        
        if cur.rowcount == 0:
            session["error_massage"] = "Invalid username or email"
            return redirect("/apology")
        
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
        return redirect("/")
        
        
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/apology")
def apology():
    error_massage = session.get("error_massage", "Unknown error")
    session["Unknown error"] = None
    return render_template("apology.html", error_massage=error_massage)


# Location
@app.route("/add_location", methods=["GET", "POST"])
def add_location():
    if not session.get("user_id"):
        return redirect("/")

    if request.method == "GET":
        return render_template("add_location.html")
    
    if request.method == "POST":
        location_name = request.form.get("location_name")
        description = request.form.get("description")

        if not location_name:
            session["error_massage"] = "You must enter a location name."
            return redirect("/apology")
        
        # Check if the location alrady exists
        cur = db.cursor(buffered=True)
        
        query = "SELECT * FROM locations WHERE location_name = %s"
        data = (location_name, )
        cur.execute(query, data)
        
        if cur.rowcount > 0:
            cur.close()
            session["error_massage"] = "The name of the river must be unique"
            return redirect("/apology")
        
        cur.close()

        cur = db.cursor(buffered=True)
        

        try: 
            # Defult lat and long
            latitude = Decimal("0.0")
            longitude = Decimal("0.0")
            
            if description:
                query = "INSERT INTO locations (user_id, location_name, description, latitude, longitude) VALUES (%s, %s, %s, %s, %s)"
                data = (session.get("user_id"), location_name, description, latitude, longitude)    
                cur.execute(query, data)
            
            else:
                query = "INSERT INTO locations (user_id, location_name, latitude, longitude) VALUES (%s, %s, %s, %s)"
                data = (session.get("user_id"), location_name, latitude, longitude)
                cur.execute(query, data)
        
        except:
            session["error_massage"] = "Location name must be less then 255 and description must be less then 6000 characters long"
            return redirect("/apology")
            
        db.commit()
        cur.close()
    # Get the id of the newly added location and
    # Redirect to the newly added location
    cur = db.cursor(buffered=True)
    
    query = "SELECT * FROM locations WHERE user_id = %s ORDER BY date_submitted DESC"
    data = (int(session["user_id"]), )
    cur.execute(query, data)
    location_id = int(cur.fetchall()[0][0])

    cur.close()
    return redirect(url_for("view", location_id=location_id))


@app.route("/edit_location", methods=["POST"])
def edit_location():
    if request.method == "POST":
        location_id = request.form.get("location_id")
        
        if not location_id:
            session["error_massage"] = "Must provide location ID"
            return redirect("/apology")
        
        cur = db.cursor(buffered=True)

        query = "SELECT * FROM locations WHERE location_id = %s"
        data = (int(location_id), )
        cur.execute(query, data)

        location = cur.fetchall()[0]
        cur.close()

        if location[1] != session["user_id"]:
            session["error_massage"] = "Only the person who uploaded the location can make chnages to it"
            return redirect("/apology")
        
        location_data = {
            "location_id" : location[0],
            "location_name" : location[2],
            "description" : location[3],
            "latitude" : location[4],
            "longitude" : location[5],
        }
        
        # To be used if no new latitude and logitude is provited
        session["old_latitude"] = location[4]
        session["old_logitude"] = location[5]

        return render_template("edit_location.html", location_data=location_data)
    

@app.route("/edit_location_function", methods=["POST"])
def edit_location_function():
    location_id = session.get("location_id")
    description = request.form.get("description")
    latitude = request.form.get("latitude")
    longitude = request.form.get("longitude")

    old_latitude = session.get("old_latitude")
    old_logitude = session.get("old_logitude")

    if len(description) > 6000:
        session["error_massage"] = "Description must be less then 6000 characters long"
        return redirect("/apology")
    
    if (latitude and not longitude) or (not latitude and longitude):
        session["error_massage"] = "Both latitude and longitude must be included to add geo location"
        return redirect("/apology")

    if latitude and longitude:
        if  not (-90 <= float(latitude) <= 90):
            session["error_massage"] = "latitude must be between (-90) and (90)"
            return redirect("/apology")
        
        if not (-180 <= float(longitude) <= 180):
            session["error_massage"] = "longitude must be between (-180) and (180)"
            return redirect("/apology")
    
        latitude = Decimal(latitude)
        longitude = Decimal(longitude)
    
    # If no lat and long is provited use old lat and long
    if not latitude and not longitude:
        latitude = Decimal(old_latitude)
        longitude = Decimal(old_logitude)

    #Updating the lcoation in database
    cur = db.cursor(buffered=True)

    query = "UPDATE locations SET description = %s, latitude = %s, longitude = %s WHERE location_id = %s"
    data = (description, latitude, longitude, int(location_id))
    cur.execute(query, data)

    db.commit()
    cur.close()

    return redirect(url_for("view", location_id=location_id))
    

# View
@app.route("/view")
def view():
    
    location_id = request.args.get("location_id")

    if not location_id:
        session["error_massage"] = "Must provide a valid location ID"
        return redirect("/apology")

    # Geting the location data    
    cur = db.cursor(buffered=True)

    try:
        query = "SELECT * FROM locations WHERE location_id = %s"
        data = (int(location_id), )
        cur.execute(query, data)

        if cur.rowcount == 0:
            session["error_massage"] = "The location you are requesting does not exist"
            cur.close()
            return redirect("/apology")
        location_data = list(cur.fetchall()[0])
        cur.close()
    
    except:
        session["error_massage"] = "The location you are requesting does not exist"
        return redirect("/apology")

    # Geting the latest data for the location
    cur = db.cursor(buffered=True)
    
    query = "SELECT * FROM data WHERE location_id = %s ORDER BY date_submitted DESC"
    data = (int(location_id), )
    cur.execute(query, data)

    # IF the the location has no data
    if cur.rowcount == 0:
        parameter_data = None
        date = None
        data_id = None
    
    else:
        # If the location exists
        # Making a list of data parameters tuple to be used in the HTML table
        data_tupe = cur.fetchall()[0]
        cur.close()
        date = data_tupe[3]
        data_id = data_tupe[0]
        parameter_data = [
            ("pH" , data_tupe[4]),
            ("BOD (mg/l)" , data_tupe[5]),
            ("COD (mg/l)" , data_tupe[6]),
            ("Temperature (ᵒC)" , data_tupe[7]),
            ("Ammonia (mg/l)" , data_tupe[8]),
            ("Arsenic (mg/l)" , data_tupe[9]),
            ("Calcium (mg/l)" , data_tupe[10]),
            ("EC (μS/cm)" , data_tupe[11]),
            ("Coliform ((Fecal) (N/100ml)" , data_tupe[12]),
            ("Hardness (mg/l)" , data_tupe[13]),
            ("Lead (mg/l)" , data_tupe[14]),
            ("Nitrogen (mg/l)" , data_tupe[15]),
            ("Sodium (mg/l)" , data_tupe[16]),
            ("Sulfate (mg/l)" , data_tupe[17]),
            ("TSS (mg/l)" , data_tupe[18]),
            ("Turbidity (NTU)" , data_tupe[19])
        ]    
    # Seting the loation lat and long to None if its 0.00
    if float(location_data[4]) == float(location_data[5]) == 0.0:
        location_data[4] = None
        location_data[5] = None

    session["location_id"] = location_data[0]
    return render_template("view.html", location_data=location_data, parameter_data=parameter_data, date=date, data_id=data_id)


# Support
@app.route("/support") 
def support():
    cur = db.cursor(buffered=True)
    
    # If the user is a Admin get all the tickets that have not been resolved yet 
    if session["user_type"] == "A":
        cur.execute("SELECT * FROM tickets WHERE status = 0")
        tickets = cur.fetchall()
    
    # If the user is a researcher or a viewer get all tickets that he has submitted
    else:
        query = "SELECT * FROM tickets WHERE user_id = %s ORDER BY date DESC"
        data = (int(session.get("user_id")), )
        cur.execute(query, data)
        tickets = cur.fetchall()

    cur.close()  
    
    return render_template("support.html", tickets=tickets)


# Shows resolved tickets (FOR ADMIN ONLY)
@app.route("/resolved_tickets")
def resolved_tickets():
    if session.get("user_type") != "A":
        session["error_massage"] = "This page is only for admins."
        return redirect("/apology")
    
    cur = db.cursor(buffered=True)
    cur.execute("SELECT * FROM tickets WHERE status = 1")
    tickets = cur.fetchall()
    cur.close()
    
    return render_template("support.html", tickets=tickets, resolve_flag=True)


@app.route("/support_form", methods=["GET", "POST"]) # Support form and support form input handaling
def submit_support():
    if request.method == "GET":
        return render_template("support_form.html")

    if request.method == "POST":
        subject = request.form.get("subject")
        description = request.form.get("description")
        user_id = session.get("user_id")

        if not subject or not description:
            session["error_massage"] = "Subject and discription is mandatory"
            return redirect("/apology")
        
        if len(subject) > 255 or len(description) > 6000:
            session["error_massage"] = "Subject can not be more then 255 characters and description can not be more then 6000 characters"
            return redirect("/apology")
            
        cur = db.cursor(buffered=True)
        
        query = "INSERT INTO tickets (user_id, subject, description) VALUES (%s, %s, %s)"
        data = (int(user_id), subject, description)
        cur.execute(query, data)

        db.commit()
        cur.close()
        
        # Geting the support id that just have been submited
        cur = db.cursor(buffered=True)

        query = "SELECT ticket_id FROM tickets WHERE user_id = %s ORDER BY date DESC LIMIT 1"
        data = (int(session.get("user_id")), )
        cur.execute(query, data)
        ticket_id = int(cur.fetchall()[0][0])

        return redirect(url_for("support_view", ticket_id=ticket_id))
    

@app.route("/support_view") # View of support ticket and masseging
def support_view(): 
    ticket_id = request.args.get("ticket_id")
    
    cur = db.cursor(buffered=True)

    query = "SELECT * FROM tickets WHERE ticket_id = %s"
    data = (ticket_id, )
    cur.execute(query, data)

    ticket_tuple = cur.fetchall()[0]
    cur.close()

    if ticket_tuple[1] != session.get("user_id") and session["user_type"] != "A":
        session["error_massage"] = "A ticket can be viewed by only the person who made it or a Admin"
        return redirect("/apology")

    if ticket_tuple[5] == 0:
        status = "Open"
        resolved = False
    else:
        status = "Resolved"
        resolved = True

    ticket_data = {
        "Status" : status,
        "Subject" : ticket_tuple[2],
        "Date" : ticket_tuple[3],
        "Description" : ticket_tuple[4],
        "ticket_id" : ticket_id[0],
        "user_id" : ticket_tuple[1],
        "resolved" : resolved
    }

    # Get all the messages of this ticket
    cur = db.cursor(buffered=True)

    query = "SELECT text, user_type, user_name, date FROM messages JOIN users ON messages.user_id = users.user_id WHERE ticket_id = %s ORDER BY date ASC"
    data = (int(ticket_id), )
    cur.execute(query, data)

    if cur.rowcount == 0:
        messeges = None
    
    else:
        messeges = cur.fetchall()
       
    cur.close()

    return render_template("support_view.html", ticket_data=ticket_data, messeges=messeges)


@app.route("/send_massage", methods=["POST"])
def send_massage():
    if request.method == "POST":
        user_id = session.get("user_id")
        ticket_id = int(request.form.get("ticket_id"))
        message = request.form.get("massage")
        

        # Checks if the ticket is closed or not
        cur = db.cursor(buffered=True)
        cur.execute("SELECT status FROM tickets WHERE ticket_id = %s", (int(ticket_id), ))
        check = cur.fetchall()[0][0]
        if int(check) == 1:
            session["error_massage"] = "Massage cant be sent to a closed ticket"
            return redirect("/apology")

        if len(message) > 2000:
            session["error_massage"] = "Sorry, We only support massage that are less then 2000 characters"
            return redirect("/apology")

        cur = db.cursor(buffered=True)
        
        query = "INSERT INTO messages (user_id, ticket_id, text) VALUES (%s, %s, %s)"
        data = (user_id, ticket_id, message)
        cur.execute(query, data)

        db.commit()
        cur.close()

        return redirect(url_for("support_view", ticket_id=ticket_id))


# Closing a ticket
@app.route("/close_ticket", methods=["POST"])
def close_ticket():
    if session["user_type"] != "A":
        session["error_massage"] = "Only a admin can close the ticket"
        return redirect("/apology")
    
    ticket_id = request.form.get("ticket_id")
    
    cur = db.cursor(buffered=True)

    query = "UPDATE tickets SET status = 1 WHERE ticket_id = %s"
    data = (int(ticket_id), )
    cur.execute(query, data)

    db.commit()
    cur.close()

    return redirect(url_for("support"))
    

@app.route("/add_data",  methods=["GET", "POST"])
def add_data():
    if request.method == "GET":
        return render_template("add_data.html")
    
    if request.method == "POST":      
        # Geting all the data from the HTML from  
        user_id = session.get("user_id")
        location_id = session.get("location_id")
    
        ph = request.form.get("ph")
        bod = request.form.get("bod")
        cod = request.form.get("cod")
        temperature = request.form.get("temperature")
        ammonia = request.form.get("ammonia")
        arsenic = request.form.get("arsenic")
        calcium = request.form.get("calcium")
        ec = request.form.get("ec")
        coliform = request.form.get("coliform")
        hardness = request.form.get("hardness")
        lead_pb = request.form.get("lead_pb")
        nitrogen = request.form.get("nitrogen")
        sodium = request.form.get("sodium")
        sulfate = request.form.get("sulfate")
        tss = request.form.get("tss")
        turbidity = request.form.get("turbidity")
        tds = request.form.get("tds")

        # Saving the data to the databas
        cur = db.cursor(buffered=True)

        query = "INSERT INTO data (location_id, user_id, ph, bod, cod, temperature, ammonia, arsenic, calcium, ec, coliform, hardness, lead_pb, nitrogen, sodium, sulfate, tss, turbidity, tds) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        data = (location_id, user_id, ph, bod, cod, temperature, ammonia, arsenic, calcium, ec, coliform, hardness, lead_pb, nitrogen, sodium, sulfate, tss, turbidity, tds)

        cur.execute(query, data)

        db.commit()
        cur.close()

        return redirect(url_for("view", location_id=location_id))


@app.route("/all_location_data")
def all_location_data():
    location_id = session["location_id"]

    cur = db.cursor(buffered=True)
    # Geting all the data of a location sorter by date
    query = "SELECT * FROM data WHERE location_id = %s ORDER BY date_submitted DESC"
    data = (int(location_id), )
    cur.execute(query, data)

    location_data = cur.fetchall()
    cur.close()

    return render_template("all_location_data.html", location_data=location_data)


@app.route("/view_data")
def view_data():
    location_id = session.get("location_id")
    data_id = request.args.get("data_id")

    try:
        # Geting location data
        cur = db.cursor(buffered=True)

        query = "SELECT * FROM locations WHERE location_id = %s LIMIT 1"
        data = (int(location_id), )
        cur.execute(query, data)

        location_data = cur.fetchall()[0]
        cur.close()

        # Geting parameter data
        cur = db.cursor(buffered=True)

        query = "SELECT * FROM data WHERE data_id = %s AND location_id = %s LIMIT 1"
        data = (int(data_id), int(location_id))
        cur.execute(query, data)

        data_tupe = cur.fetchall()[0]
        cur.close()

        # Making a list of data parameters tuple to be used in the HTML table
        date = data_tupe[3]
        parameter_data = [
            ("Ph" , data_tupe[4]),
            ("BOD" , data_tupe[5]),
            ("COD" , data_tupe[6]),
            ("Temperature" , data_tupe[7]),
            ("Ammonia" , data_tupe[8]),
            ("Arsenic" , data_tupe[9]),
            ("Calcium" , data_tupe[10]),
            ("EC" , data_tupe[11]),
            ("Coliform" , data_tupe[12]),
            ("Hardness" , data_tupe[13]),
            ("Lead" , data_tupe[14]),
            ("Nitrogen" , data_tupe[15]),
            ("Sodium" , data_tupe[16]),
            ("Sulfate" , data_tupe[17]),
            ("Tss" , data_tupe[18]),
            ("Turbidity" , data_tupe[19]),
            ("Tds", data_tupe[20])
        ] 

    except:
        session["error_massage"] = "API abuse or SQL erro please contact the admins"
        return redirect("/apology")

    return render_template("view.html", location_data=location_data, parameter_data=parameter_data, date=date, data_id=data_tupe[0])


@app.route("/compare_between_data", methods=["GET", "POST"])
def compare_between():
    if request.method == "GET":
        location_id = session.get("location_id")

        # Geting all the data of the location
        cur = db.cursor(buffered=True)

        query = "SELECT * FROM data WHERE location_id = %s ORDER BY date_submitted DESC"
        data = (int(location_id), )
        cur.execute(query, data)

        data_list = cur.fetchall()
        cur.close()

        return render_template("compare_between.html", data_list=data_list)
    
    if request.method == "POST":
        location_id = session.get("location_id")
        data_id_1 = request.form.get("data_id_1")
        data_id_2 = request.form.get("data_id_2")

        compare_in = request.form.get("compare_in")

        # Getting location data
        cur = db.cursor(buffered=True)

        query = "SELECT * FROM locations WHERE location_id = %s"
        data = (int(location_id), )

        cur.execute(query, data)
        location_data_tuple = cur.fetchall()[0]
        cur.close()

        # Making a location data dict
        location_data = {
            "location_id" : location_data_tuple[0],
            "location_name" : location_data_tuple[2],
            "description" : location_data_tuple[3]
        }

        # Getting data for data_id_1
        cur = db.cursor(buffered=True)

        query = "SELECT * FROM data WHERE data_id = %s"
        data = (int(data_id_1), )

        cur.execute(query, data)
        data_tupe = cur.fetchall()[0]
        cur.close()

        # Getting data for data_id_2
        cur = db.cursor(buffered=True)

        query = "SELECT * FROM data WHERE data_id = %s"
        data = (int(data_id_2), )

        cur.execute(query, data)
        data_tupe_2 = cur.fetchall()[0]
        cur.close()
        date = [data_tupe[3], data_tupe_2[3]]
        # Making a list of data parameters tuple to be used in the HTML table
        if compare_in == "table":
            parameter_data = [
            ("Ph" , data_tupe[4], data_tupe_2[4]),
            ("BOD (mg/ml)" , data_tupe[5], data_tupe_2[5]),
            ("COD (mg/ml)" , data_tupe[6], data_tupe_2[6]),
            ("Temperature (ᵒC)" , data_tupe[7], data_tupe_2[7]),
            ("Ammonia (mg/ml)" , data_tupe[8], data_tupe_2[8]),
            ("Arsenic (mg/ml)" , data_tupe[9], data_tupe_2[9]),
            ("Calcium (mg/ml)" , data_tupe[10], data_tupe_2[10]),
            ("EC (µS/cm)" , data_tupe[11], data_tupe_2[11]),
            ("Coliform (Faecal) (N/100ml)" , data_tupe[12], data_tupe_2[12]),
            ("Hardness (mg/ml)" , data_tupe[13], data_tupe_2[13]),
            ("Lead (mg/ml)" , data_tupe[14], data_tupe_2[14]),
            ("Nitrogen (mg/ml)" , data_tupe[15], data_tupe_2[15]),
            ("Sodium (mg/ml)" , data_tupe[16], data_tupe_2[16]),
            ("Sulfate (mg/ml)" , data_tupe[17], data_tupe_2[17]),
            ("Tss (mg/ml)" , data_tupe[18], data_tupe_2[18]),
            ("Turbidity (NTU)" , data_tupe[19], data_tupe_2[19]),
            ("Tds (mg/ml)", data_tupe[20], data_tupe_2[20])
            ]

            return render_template("table_compare.html", location_data=location_data , parameter_data=parameter_data, date=date)
        # Making 2 python dicts contaning all the data parameters from 2 data sets
        # The dicts will be converted into JSON files in Jinja to used by graphs
        if compare_in == "graph":
            location_1_data = {
            "ph": data_tupe[4],
            "bod": data_tupe[5],
            "cod": data_tupe[6],
            "temperature": data_tupe[7], 
            "ammonia" : data_tupe[8],
            "arsenic" : data_tupe[9],
            "calcium": data_tupe[10],
            "ec" : data_tupe[11],
            "coliform": data_tupe[12],
            "hardness": data_tupe[13],
            "lead_pb": data_tupe[14],
            "nitrogen": data_tupe[15],
            "sodium": data_tupe[16],
            "sulfate" : data_tupe[17],
            "tss": data_tupe[18],
            "turbidity": data_tupe[19],
            "tds" : data_tupe[20]
            }

            location_2_data = {
            "ph": data_tupe_2[4],
            "bod": data_tupe_2[5],
            "cod": data_tupe_2[6],
            "temperature": data_tupe_2[7], 
            "ammonia" : data_tupe_2[8],
            "arsenic" : data_tupe_2[9],
            "calcium": data_tupe_2[10],
            "ec" : data_tupe_2[11],
            "coliform": data_tupe_2[12],
            "hardness": data_tupe_2[13],
            "lead_pb": data_tupe_2[14],
            "nitrogen": data_tupe_2[15],
            "sodium": data_tupe_2[16],
            "sulfate" : data_tupe_2[17],
            "tss": data_tupe_2[18],
            "turbidity": data_tupe_2[19],
            "tds" : data_tupe_2[20]
            }

            date_dic = {
                "left" : date[0],
                "right" : date[1]
            }

            return render_template("graph_compare.html", location_1_data=location_1_data, location_2_data=location_2_data, date_dic=date_dic, location_data=location_data)


@app.route("/compare_between_locations", methods=["GET", "POST"])
def compare_between_locations():
    if request.method == "GET":
        # Getting all the location that have at least 1 data submitted to them 
        cur = db.cursor(buffered=True)
        query = "SELECT location_id, location_name FROM locations WHERE location_id IN (SELECT location_id FROM data) ORDER BY location_name"
        data = ()
        cur.execute(query, data)

        locations_tuple_liist = cur.fetchall()
        cur.close()

        locations_dict_list = []
        for tuple in locations_tuple_liist:
            locations_dict_list.append({
                "location_id" : tuple[0],
                "location_name" : tuple[1]
            })

        return render_template("compare_between_locations.html", locations=locations_dict_list)
    
    if request.method == "POST":
        location_id_1 = request.form.get("location_id_1")
        location_id_2 = request.form.get("location_id_2")

        if location_id_1 == location_id_2:
            session["error_massage"] = "You have selected the same location to compare, please select diffrent locations"
            return redirect("/apology")

        # Getting location name
        cur = db.cursor(buffered=True)
        
        query = "SELECT location_name FROM locations WHERE location_id IN (%s, %s)"
        data = (int(location_id_1), int(location_id_2))
        cur.execute(query, data)

        locations_list_tupe = cur.fetchall()
        cur.close()

        location_data = {
            "location_name_1" : locations_list_tupe[0][0],
            "location_name_2" : locations_list_tupe[1][0]
        }

        compare_in = request.form.get("compare_in")
        
        # Geting data for location 1 
        cur = db.cursor(buffered=True)

        query = "SELECT * FROM data WHERE location_id = %s ORDER BY date_submitted DESC LIMIT 1"
        data = (int(location_id_1), )
        cur.execute(query, data)

        data_tupe = cur.fetchall()[0]
        cur.close()

        # Geting data for location 2
        cur = db.cursor(buffered=True)

        query = "SELECT * FROM data WHERE location_id = %s ORDER BY date_submitted DESC LIMIT 1"
        data = (int(location_id_2), )
        cur.execute(query, data)

        data_tupe_2 = cur.fetchall()[0]
        cur.close()

        if compare_in == "table":   
            # Making a list of data parameters tuple to be used in the HTML table        
            parameter_data = [
            ("Ph" , data_tupe[4], data_tupe_2[4]),
            ("BOD (mg/ml)" , data_tupe[5], data_tupe_2[5]),
            ("COD (mg/ml)" , data_tupe[6], data_tupe_2[6]),
            ("Temperature (ᵒC)" , data_tupe[7], data_tupe_2[7]),
            ("Ammonia (mg/ml)" , data_tupe[8], data_tupe_2[8]),
            ("Arsenic (mg/ml)" , data_tupe[9], data_tupe_2[9]),
            ("Calcium (mg/ml)" , data_tupe[10], data_tupe_2[10]),
            ("EC (µS/cm)" , data_tupe[11], data_tupe_2[11]),
            ("Coliform (Faecal) (N/100ml)" , data_tupe[12], data_tupe_2[12]),
            ("Hardness (mg/ml)" , data_tupe[13], data_tupe_2[13]),
            ("Lead (mg/ml)" , data_tupe[14], data_tupe_2[14]),
            ("Nitrogen (mg/ml)" , data_tupe[15], data_tupe_2[15]),
            ("Sodium (mg/ml)" , data_tupe[16], data_tupe_2[16]),
            ("Sulfate (mg/ml)" , data_tupe[17], data_tupe_2[17]),
            ("Tss (mg/ml)" , data_tupe[18], data_tupe_2[18]),
            ("Turbidity (NTU)" , data_tupe[19], data_tupe_2[19]),
            ("Tds (mg/ml)", data_tupe[20], data_tupe_2[20])
            ]

            return render_template("compare_between_locations_table.html", parameter_data=parameter_data, location_data=location_data)
        
        if compare_in == "graph":
        # Making 2 python dicts contaning all the data parameters from 2 data sets
        # The dicts will be converted into JSON files in Jinja to used by graphs
            location_1_data = {
            "ph": data_tupe[4],
            "bod": data_tupe[5],
            "cod": data_tupe[6],
            "temperature": data_tupe[7], 
            "ammonia" : data_tupe[8],
            "arsenic" : data_tupe[9],
            "calcium": data_tupe[10],
            "ec" : data_tupe[11],
            "coliform": data_tupe[12],
            "hardness": data_tupe[13],
            "lead_pb": data_tupe[14],
            "nitrogen": data_tupe[15],
            "sodium": data_tupe[16],
            "sulfate" : data_tupe[17],
            "tss": data_tupe[18],
            "turbidity": data_tupe[19],
            "tds" : data_tupe[20]
            }

            location_2_data = {
            "ph": data_tupe_2[4],
            "bod": data_tupe_2[5],
            "cod": data_tupe_2[6],
            "temperature": data_tupe_2[7], 
            "ammonia" : data_tupe_2[8],
            "arsenic" : data_tupe_2[9],
            "calcium": data_tupe_2[10],
            "ec" : data_tupe_2[11],
            "coliform": data_tupe_2[12],
            "hardness": data_tupe_2[13],
            "lead_pb": data_tupe_2[14],
            "nitrogen": data_tupe_2[15],
            "sodium": data_tupe_2[16],
            "sulfate" : data_tupe_2[17],
            "tss": data_tupe_2[18],
            "turbidity": data_tupe_2[19],
            "tds" : data_tupe_2[20]
            }

            return render_template("compare_between_locations_graph.html", location_data=location_data, location_1_data=location_1_data, location_2_data=location_2_data)
        

# Profile 
@app.route("/profile")
def profile():
    # Geting all the data of the logged in user
    cur = db.cursor(buffered=True)
    cur.execute("SELECT * FROM users WHERE user_id = %s", (int(session.get("user_id")), ))
    user_tuple = cur.fetchall()[0]
    cur.close()

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


@app.route("/edit_profile", methods=["GET", "POST"])
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
        cur = db.cursor(buffered=True)
        cur.execute("SELECT * FROM users WHERE user_id = %s", (session.get("user_id"), ))
        user_data_old = cur.fetchall()[0]
        cur.close()

        user_data_new = {}

        if not email:
            user_data_new["email"] = user_data_old[2]
        else:
            # Cheks if email exists or not
            cur = db.cursor(buffered=True)
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
        cur = db.cursor(buffered=True)
        query = "UPDATE users SET email = %s, latitude = %s, longitude = %s, first_name = %s, last_name = %s WHERE user_id = %s"
        data = (user_data_new["email"], user_data_new["latitude"], user_data_new["longitude"], user_data_new["first_name"], user_data_new["last_name"], session.get("user_id"))
        cur.execute(query, data)
        db.commit()
        cur.close()
        
        return redirect(url_for("profile"))


@app.route("/change_password", methods=["GET", "POST"])
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
        
        cur = db.cursor(buffered=True)
        cur.execute("SELECT password_hash FROM users WHERE user_id = %s", (session.get("user_id"), ))
        
        # Checking if the privious password is correct
        if check_password_hash(cur.fetchall()[0][0], old_password):
            cur.close()
            cur = db.cursor(buffered=True)
            cur.execute("UPDATE users SET password_hash = %s WHERE user_id = %s", (
                str(generate_password_hash(password)),
                session.get("user_id")
            ))
            db.commit()
            cur.close()

        else:
            session["error_massage"] = "Incorrect Password, please try again"
            return redirect("/apology")

        return redirect(url_for("profile"))


# Admin Views
# Edit pages are implimented as the edit profile page 
@app.route("/admin")
def admin():
    if session.get("user_type") != "A":
        session["error_massage"] = "This page is only for admins."
        return redirect("/apology")
    
    return render_template("admin.html")


@app.route("/admin_users")
def admin_users():
    if session.get("user_type") != "A":
        session["error_massage"] = "This page is only for admins."
        return redirect("/apology")
    
    # Gets all the user (excluding the admins)
    cur = db.cursor(buffered=True)
    cur.execute("SELECT user_id, user_name, user_type FROM users WHERE user_type != 'A'")
    users = cur.fetchall()
    
    return render_template("admin_user.html", users=users)


@app.route("/admin_user_edit", methods=["GET", "POST"])
def admin_user_edit():
    if session.get("user_type") != "A":
        session["error_massage"] = "This page is only for admins."
        return redirect("/apology")
    
    user_id = request.args.get("user_id")

    if request.method == "GET":
        
        cur = db.cursor(buffered=True)
        cur.execute("SELECT user_name, email, latitude, longitude, first_name, last_name, user_type FROM users WHERE user_id = %s", (int(user_id), ))
        user_data = cur.fetchall()[0]

        return render_template("admin_user_edit.html", user_data=user_data, user_id=user_id)
    
    if request.method == "POST":
        user_id = request.form.get("user_id")
        user_name = request.form.get("user_name")
        email = request.form.get("email")
        password = request.form.get("password")
        password_again = request.form.get("password_again")
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        user_type = request.form.get("user_type")

        if user_name:
            # See if username taken
            cur = db.cursor(buffered=True)
            cur.execute("SELECT * FROM users WHERE user_name = %s", (user_name, ))
            if cur.rowcount > 0:
                cur.close()
                session["error_massage"] = "Username allready exits"
                return redirect("/apology")
            else:
                cur.close()
                cur = db.cursor(buffered=True)
                cur.execute("UPDATE users SET user_name = %s WHERE user_id = %s", (user_name, user_id))
                db.commit()
                cur.close()

        if email:
            # See if email taken
            cur = db.cursor(buffered=True)
            cur.execute("SELECT * FROM users WHERE email = %s", (email, ))
            if cur.rowcount > 0:
                cur.close()
                session["error_massage"] = "Email is allready in use"
                return redirect("/apology")
            else:
                cur.close()
                cur = db.cursor(buffered=True)
                cur.execute("UPDATE users SET email = %s WHERE user_id = %s", (email, user_id))
                db.commit()
                cur.close()

        if password:
            if password != password_again:
                session["error_massage"] = "Confirmation dose not match"
                return redirect("/apology")
            
            cur = db.cursor(buffered=True)
            cur.execute("UPDATE users SET password_hash = %s WHERE user_id = %s", (generate_password_hash(password), user_id))
            db.commit()
            cur.close()

        if latitude:
            if  not (-90 <= float(latitude) <= 90):
                session["error_massage"] = "latitude must be between (-90) and (90)"
                return redirect("/apology")

            cur = db.cursor(buffered=True)
            cur.execute("UPDATE users SET latitude = %s WHERE user_id = %s", (Decimal(latitude), user_id))
            db.commit()
            cur.close()
        
        if longitude:
            if not (-180 <= float(longitude) <= 180):
                session["error_massage"] = "longitude must be between (-180) and (180)"
                return redirect("/apology")

            cur = db.cursor(buffered=True)
            cur.execute("UPDATE users SET longitude = %s WHERE user_id = %s", (Decimal(longitude), user_id))
            db.commit()
            cur.close()

        if first_name:
            if len(first_name) > 255:
                session["error_massage"] = "First name must be less then 255 characters"
                return redirect("/apology")
            
            cur = db.cursor(buffered=True)
            cur.execute("UPDATE users SET first_name = %s WHERE user_id = %s", (first_name, user_id))
            db.commit()
            cur.close()

        if last_name:
            if len(last_name) > 255:
                session["error_massage"] = "Last name must be less then 255 characters"
                return redirect("/apology")
            
            cur = db.cursor(buffered=True)
            cur.execute("UPDATE users SET last_name = %s WHERE user_id = %s", (last_name, user_id))
            db.commit()
            cur.close()

        if user_type:
            if user_type not in ["V", "R"]:
                session["error_massage"] = "Invalid user type"
                return redirect("/apology")
            
            cur = db.cursor(buffered=True)
            cur.execute("UPDATE users SET user_type = %s WHERE user_id = %s", (user_type, user_id))
            db.commit()
            cur.close()
 
        return redirect(url_for("admin_user_edit", user_id=user_id))


@app.route("/admin_locations")
def admin_locations():
    if session.get("user_type") != "A":
        session["error_massage"] = "This page is only for admins."
        return redirect("/apology")

    cur = db.cursor(buffered=True)
    cur.execute("SELECT location_id, location_name, date_submitted FROM locations")
    locations = cur.fetchall()
    
    return render_template("admin_location.html", locations=locations)


@app.route("/admin_location_edit", methods=["GET", "POST"])
def admin_location_edit():
    if session.get("user_type") != "A":
        session["error_massage"] = "This page is only for admins."
        return redirect("/apology")
    
    location_id = request.args.get("location_id")

    if request.method == "GET":

        cur = db.cursor(buffered=True)
        cur.execute("SELECT location_name, description, latitude, longitude FROM locations WHERE location_id = %s", (location_id, ))
        location_data = cur.fetchall()[0]

        return render_template("admin_location_edit.html", location_data=location_data, location_id=location_id)
    
    if request.method == "POST":
        location_id = request.form.get("location_id")
        location_name = request.form.get("location_name")
        description = request.form.get("description")
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")

        if location_name:
            if len(location_name) > 255:
                session["error_massage"] = "Location name must be less then 255 chracters"
                return redirect("/apology")
            
            cur = db.cursor(buffered=True)
            cur.execute("SELECT * FROM locations WHERE location_name = %s", (location_name, ))
            if cur.rowcount > 0:
                cur.close()
                session["error_massage"] = "Location name taken"
                return redirect("/apology")
           
            cur = db.cursor(buffered=True)
            cur.execute("UPDATE locations SET location_name = %s WHERE location_id = %s", (location_name, location_id))
            db.commit()
            cur.close()

        if description:
            if len(description) > 6000:
                session["error_massage"] = "Description must be less then 6000 chracters"
                return redirect("/apology")
            
            cur = db.cursor(buffered=True)
            cur.execute("UPDATE locations SET description = %s WHERE location_id = %s", (description, location_id))
            db.commit()
            cur.close()

        if latitude:
            if  not (-90 <= float(latitude) <= 90):
                session["error_massage"] = "latitude must be between (-90) and (90)"
                return redirect("/apology")

            cur = db.cursor(buffered=True)
            cur.execute("UPDATE locations SET latitude = %s WHERE location_id = %s", (Decimal(latitude), location_id))
            db.commit()
            cur.close()
        
        if longitude:
            if not (-180 <= float(longitude) <= 180):
                session["error_massage"] = "longitude must be between (-180) and (180)"
                return redirect("/apology")

            cur = db.cursor(buffered=True)
            cur.execute("UPDATE locations SET longitude = %s WHERE location_id = %s", (Decimal(longitude), location_id))
            db.commit()
            cur.close()

        return redirect(url_for("admin_location_edit", location_id=location_id))


@app.route("/random_location")
def random_location():
    if not session.get("user_id"):
        redirect(url_for("login"))

    cur = db.cursor(buffered=True)
    cur.execute("SELECT location_id FROM locations")
    locations = cur.fetchall()

    random_location_id = (random.choice(locations))[0]

    return redirect(url_for("view", location_id=random_location_id))


# Delete
@app.route("/delete_user", methods=["POST"])
def delete_user():
    if session.get("user_type") != "A":
        session["error_massage"] = "This page is only for admins."
        return redirect("/apology")
    
    user_id = request.form.get("user_id")
    
    if user_id:
        cur = db.cursor(buffered=True)
        cur.execute("DELETE FROM users WHERE user_id = %s", (int(user_id), ))
        db.commit()
        cur.close()

        return redirect(url_for("admin_users"))
    
    else:
        return "INVALID REQUSET"
    

@app.route("/delete_location", methods=["POST"])
def delete_location():
    if session.get("user_type") != "A":
        session["error_massage"] = "This page is only for admins."
        return redirect("/apology")
    
    location_id = request.form.get("location_id")
    
    if location_id:
        cur = db.cursor(buffered=True)
        cur.execute("DELETE FROM locations WHERE location_id = %s", (int(location_id), ))
        db.commit()
        cur.close()

        return redirect(url_for("admin_locations"))
    
    else:
        return "INVALID REQUSET"
    

@app.route("/delete_data", methods=["POST"])
def delete_data():
    if session.get("user_type") != "A":
        session["error_massage"] = "This page is only for admins."
        return redirect("/apology")
    
    data_id = request.form.get("data_id")
    location_id = request.form.get("location_id")
    
    if data_id and location_id:
        cur = db.cursor(buffered=True)
        cur.execute("DELETE FROM data WHERE data_id = %s", (int(data_id), ))
        db.commit()
        cur.close()

        return redirect(url_for("view", location_id=location_id))
    
    else:
        return "INVALID REQUSET"
    

# Add this at the end of the file
if __name__ == "__main__":
    app.run(debug=True)
    