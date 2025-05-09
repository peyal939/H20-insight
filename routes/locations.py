from flask import Blueprint, request, render_template, session, redirect, url_for
from decimal import Decimal
from models.db import get_cursor, DatabaseConnection

# Create locations blueprint - manages all location-related functionality
locations_bp = Blueprint('locations', __name__)

@locations_bp.route("/add_location", methods=["GET", "POST"])
def add_location():
    """
    Handles the creation of new water monitoring locations.
    GET: Displays the location creation form.
    POST: Processes the form submission, adding the location to the database.
    
    Also handles optional initial water quality data that can be submitted
    with a new location.
    """
    # Redirect to home if user is not logged in
    if not session.get("user_id"):
        return redirect("/")

    if request.method == "GET":
        # Display the location creation form
        return render_template("add_location.html")
    
    if request.method == "POST":
        # Process form submission to create a new location
        
        # Get location details from form
        location_name = request.form.get("location_name")
        description = request.form.get("description")

        # Validate location name is provided
        if not location_name:
            session["error_massage"] = "You must enter a location name."
            return redirect(url_for("auth.apology"))
        
        # Check if the location already exists
        try:
            with DatabaseConnection() as (cur, db):
                query = "SELECT * FROM locations WHERE location_name = %s"
                data = (location_name, )
                cur.execute(query, data)
                
                if cur.rowcount > 0:
                    session["error_massage"] = "The name of the river must be unique"
                    return redirect(url_for("auth.apology"))
        except Exception as e:
            session["error_massage"] = f"Error checking location name: {str(e)}"
            return redirect(url_for("auth.apology"))

        try: 
            # Set default latitude and longitude to 0.0
            latitude = Decimal("0.0")
            longitude = Decimal("0.0")
            
            with DatabaseConnection() as (cur, db):
                # Insert new location with or without description
                if description:
                    query = "INSERT INTO locations (user_id, location_name, description, latitude, longitude) VALUES (%s, %s, %s, %s, %s)"
                    data = (session.get("user_id"), location_name, description, latitude, longitude)    
                    cur.execute(query, data)
                
                else:
                    query = "INSERT INTO locations (user_id, location_name, latitude, longitude) VALUES (%s, %s, %s, %s)"
                    data = (session.get("user_id"), location_name, latitude, longitude)
                    cur.execute(query, data)
                
                # Commit the new location to the database
                db.commit()
                
                # Get the ID of the newly added location
                query = "SELECT * FROM locations WHERE user_id = %s ORDER BY date_submitted DESC"
                data = (int(session["user_id"]), )
                cur.execute(query, data)
                location_id = int(cur.fetchall()[0][0])
        
        except Exception as e:
            # Handle errors related to data length or other database issues
            session["error_massage"] = f"Error adding location: {str(e)}"
            return redirect(url_for("auth.apology"))
        
        # Check if water parameters were provided with the new location
        has_water_data = any([
            request.form.get("ph"), request.form.get("bod"), 
            request.form.get("cod"), request.form.get("temperature"),
            request.form.get("ammonia"), request.form.get("arsenic"),
            request.form.get("calcium"), request.form.get("ec"),
            request.form.get("coliform"), request.form.get("hardness"),
            request.form.get("lead_pb"), request.form.get("nitrogen"),
            request.form.get("sodium"), request.form.get("sulfate"),
            request.form.get("tss"), request.form.get("turbidity"),
            request.form.get("tds")
        ])
        
        # If water data is provided, save it to data table
        if has_water_data:
            user_id = session.get("user_id")
            
            # Function to safely convert values to float or None
            def safe_float(value):
                if value is None or value == "":
                    return None
                try:
                    return float(value)
                except ValueError:
                    return None
            
            # Get form values and convert them safely to float
            ph = safe_float(request.form.get("ph"))
            bod = safe_float(request.form.get("bod"))
            cod = safe_float(request.form.get("cod"))
            temperature = safe_float(request.form.get("temperature"))
            ammonia = safe_float(request.form.get("ammonia"))
            arsenic = safe_float(request.form.get("arsenic"))
            calcium = safe_float(request.form.get("calcium"))
            ec = safe_float(request.form.get("ec"))
            coliform = safe_float(request.form.get("coliform"))
            hardness = safe_float(request.form.get("hardness"))
            lead_pb = safe_float(request.form.get("lead_pb"))
            nitrogen = safe_float(request.form.get("nitrogen"))
            sodium = safe_float(request.form.get("sodium"))
            sulfate = safe_float(request.form.get("sulfate"))
            tss = safe_float(request.form.get("tss"))
            turbidity = safe_float(request.form.get("turbidity"))
            tds = safe_float(request.form.get("tds"))
            
            # Validate pH is within valid range (0-14)
            if ph is not None and (ph < 0 or ph > 14):
                session["error_massage"] = "pH value must be between 0 and 14"
                return redirect(url_for("auth.apology"))

            try:
                # Save the water quality data to the database
                with DatabaseConnection() as (cur, db):
                    query = "INSERT INTO data (location_id, user_id, ph, bod, cod, temperature, ammonia, arsenic, calcium, ec, coliform, hardness, lead_pb, nitrogen, sodium, sulfate, tss, turbidity, tds) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                    data = (location_id, user_id, ph, bod, cod, temperature, ammonia, arsenic, calcium, ec, coliform, hardness, lead_pb, nitrogen, sodium, sulfate, tss, turbidity, tds)
                    cur.execute(query, data)
                    db.commit()
            except Exception as e:
                session["error_massage"] = f"Error saving water quality data: {str(e)}"
                return redirect(url_for("auth.apology"))

        # Redirect to view the newly created location
        return redirect(url_for("locations.view", location_id=location_id))

@locations_bp.route("/edit_location", methods=["POST"])
def edit_location():
    """
    Initiates the location editing process.
    Validates that the user is the creator of the location.
    Displays the edit form with current location data.
    """
    if request.method == "POST":
        # Get location ID from form data
        location_id = request.form.get("location_id")
        
        # Validate location ID is provided
        if not location_id:
            session["error_massage"] = "Must provide location ID"
            return redirect("/apology")
        
        # Get location data from database
        cur, db = get_cursor()

        query = "SELECT * FROM locations WHERE location_id = %s"
        data = (int(location_id), )
        cur.execute(query, data)

        location = cur.fetchall()[0]
        cur.close()
        db.close()

        # Verify user is the owner of the location
        if location[1] != session["user_id"]:
            session["error_massage"] = "Only the person who uploaded the location can make chnages to it"
            return redirect("/apology")
        
        # Format location data for the edit form
        location_data = {
            "location_id" : location[0],
            "location_name" : location[2],
            "description" : location[3],
            "latitude" : location[4],
            "longitude" : location[5],
        }
        
        # Store original coordinates in session in case no new ones are provided
        session["old_latitude"] = location[4]
        session["old_logitude"] = location[5]

        return render_template("edit_location.html", location_data=location_data)

@locations_bp.route("/edit_location_function", methods=["POST"])
def edit_location_function():
    """
    Processes the location edit form submission.
    Updates the location data in the database.
    Validates coordinate data if provided.
    """
    # Get form data
    location_id = session.get("location_id")
    description = request.form.get("description")
    latitude = request.form.get("latitude")
    longitude = request.form.get("longitude")

    # Get original coordinates from session
    old_latitude = session.get("old_latitude")
    old_logitude = session.get("old_logitude")

    # Validate description length
    if len(description) > 6000:
        session["error_massage"] = "Description must be less then 6000 characters long"
        return redirect("/apology")
    
    # Ensure both latitude and longitude are provided together
    if (latitude and not longitude) or (not latitude and longitude):
        session["error_massage"] = "Both latitude and longitude must be included to add geo location"
        return redirect("/apology")

    # Validate coordinate values if provided
    if latitude and longitude:
        if not (-90 <= float(latitude) <= 90):
            session["error_massage"] = "latitude must be between (-90) and (90)"
            return redirect("/apology")
        
        if not (-180 <= float(longitude) <= 180):
            session["error_massage"] = "longitude must be between (-180) and (180)"
            return redirect("/apology")
    
        # Convert coordinates to Decimal for database
        latitude = Decimal(latitude)
        longitude = Decimal(longitude)
    
    # If no new coordinates provided, use original ones
    if not latitude and not longitude:
        latitude = Decimal(old_latitude)
        longitude = Decimal(old_logitude)

    # Update the location in database
    cur, db = get_cursor()

    query = "UPDATE locations SET description = %s, latitude = %s, longitude = %s WHERE location_id = %s"
    data = (description, latitude, longitude, int(location_id))
    cur.execute(query, data)

    db.commit()
    cur.close()
    db.close()

    # Redirect to view the updated location
    return redirect(url_for("locations.view", location_id=location_id))

@locations_bp.route("/view")
def view():
    """
    Displays a specific location and its most recent water quality data.
    Shows location details and the most recent data measurements.
    """
    # Get location ID from URL parameters
    location_id = request.args.get("location_id")

    # Validate location ID is provided
    if not location_id:
        session["error_massage"] = "Must provide a valid location ID"
        return redirect(url_for("auth.apology"))

    try:
        # Get the location data from database
        with DatabaseConnection() as (cur, db):
            query = "SELECT * FROM locations WHERE location_id = %s"
            data = (int(location_id), )
            cur.execute(query, data)

            # Check if location exists
            if cur.rowcount == 0:
                session["error_massage"] = "The location you are requesting does not exist"
                return redirect(url_for("auth.apology"))
            
            # Get location data
            location_data = list(cur.fetchall()[0])
            
            # Get the latest water quality data for the location
            query = "SELECT * FROM data WHERE location_id = %s ORDER BY date_submitted DESC"
            data = (int(location_id), )
            cur.execute(query, data)

            # If the location has no water quality data
            if cur.rowcount == 0:
                parameter_data = None
                date = None
                data_id = None
            else:
                # If water quality data exists
                # Create a list of data parameters for the HTML table
                data_tupe = cur.fetchall()[0]
                date = data_tupe[3]  # Date submitted
                data_id = data_tupe[0]  # Data ID
                
                # Format data for display with proper units - fix inconsistent labels
                parameter_data = [
                    ("pH", data_tupe[4]),
                    ("BOD (mg/l)", data_tupe[5]),
                    ("COD (mg/l)", data_tupe[6]),
                    ("Temperature (ᵒC)", data_tupe[7]),
                    ("Ammonia (mg/l)", data_tupe[8]),
                    ("Arsenic (mg/l)", data_tupe[9]),
                    ("Calcium (mg/l)", data_tupe[10]),
                    ("EC (μS/cm)", data_tupe[11]),
                    ("Coliform (Fecal) (N/100ml)", data_tupe[12]),
                    ("Hardness (mg/l)", data_tupe[13]),
                    ("Lead (mg/l)", data_tupe[14]),
                    ("Nitrogen (mg/l)", data_tupe[15]),
                    ("Sodium (mg/l)", data_tupe[16]),
                    ("Sulfate (mg/l)", data_tupe[17]),
                    ("TSS (mg/l)", data_tupe[18]),
                    ("Turbidity (NTU)", data_tupe[19]),
                    ("TDS (mg/l)", data_tupe[20])
                ]    
    except ValueError:
        # Handle invalid location ID format
        session["error_massage"] = "Invalid location ID format"
        return redirect(url_for("auth.apology"))
    except Exception as e:
        # Handle other errors
        session["error_massage"] = f"Error retrieving location data: {str(e)}"
        return redirect(url_for("auth.apology"))
        
    # Set location coordinates to None if they're default values (0.00)
    if float(location_data[4]) == float(location_data[5]) == 0.0:
        location_data[4] = None
        location_data[5] = None

    # Store location ID in session for other routes to use
    session["location_id"] = location_data[0]
    
    # Render the view template with all location and water quality data
    return render_template("view.html", location_data=location_data, parameter_data=parameter_data, date=date, data_id=data_id) 