from flask import Blueprint, request, render_template, session, redirect, url_for, send_file
from models.db import get_cursor, DatabaseConnection
from utils.water_quality import analyze_water_quality
from utils.pdf_generator import generate_water_quality_report
import os

# Create data blueprint - manages all water quality data functionality
data_bp = Blueprint('data', __name__)

# -------------------------------------------------------------------------
# DATA COLLECTION ROUTES
# -------------------------------------------------------------------------

@data_bp.route("/add_data",  methods=["GET", "POST"])
def add_data():
    """
    Handles adding new water quality data for an existing location.
    GET: Displays the data input form.
    POST: Processes the form data and saves measurements to the database.
    """
    if request.method == "GET":
        # Display the data input form
        return render_template("add_data.html")
    
    if request.method == "POST":      
        # Get user ID and location ID from session
        user_id = session.get("user_id")
        location_id = session.get("location_id")
    
        # Function to safely convert string values to float or None
        # Prevents data truncation errors in MySQL
        def safe_float(value):
            if value is None or value == "":
                return None
            try:
                return float(value)
            except ValueError:
                return None

        # Get form values and convert them safely to float
        # Each parameter is properly converted to avoid database type errors
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

        # Use a context manager to ensure database connection is properly closed
        try:
            with DatabaseConnection() as (cur, db):
                query = "INSERT INTO data (location_id, user_id, ph, bod, cod, temperature, ammonia, arsenic, calcium, ec, coliform, hardness, lead_pb, nitrogen, sodium, sulfate, tss, turbidity, tds) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                data = (location_id, user_id, ph, bod, cod, temperature, ammonia, arsenic, calcium, ec, coliform, hardness, lead_pb, nitrogen, sodium, sulfate, tss, turbidity, tds)
                cur.execute(query, data)
                db.commit()
        except Exception as e:
            session["error_massage"] = f"Error saving data: {str(e)}"
            return redirect(url_for("auth.apology"))

        # Redirect to view the location with the new data
        return redirect(url_for("locations.view", location_id=location_id))


# -------------------------------------------------------------------------
# DATA VIEWING ROUTES
# -------------------------------------------------------------------------

@data_bp.route("/all_location_data")
def all_location_data():
    """
    Displays all water quality data entries for a specific location.
    Results are ordered by date (newest first).
    """
    # Get location ID from session
    location_id = session["location_id"]

    cur, db = get_cursor()
    # Get all data for a location ordered by date (newest first)
    query = "SELECT * FROM data WHERE location_id = %s ORDER BY date_submitted DESC"
    data = (int(location_id), )
    cur.execute(query, data)

    location_data = cur.fetchall()
    cur.close()
    db.close()

    # Render template with all data entries
    return render_template("all_location_data.html", location_data=location_data)


@data_bp.route("/view_data")
def view_data():
    """
    Displays a specific water quality data entry.
    Shows all parameters in a formatted table.
    """
    # Get location ID from session and data ID from URL parameter
    location_id = session.get("location_id")
    data_id = request.args.get("data_id")

    try:
        # Get location information
        cur, db = get_cursor()

        query = "SELECT * FROM locations WHERE location_id = %s LIMIT 1"
        data = (int(location_id), )
        cur.execute(query, data)

        location_data = cur.fetchall()[0]
        cur.close()
        db.close()

        # Get specific water quality data entry
        cur, db = get_cursor()

        query = "SELECT * FROM data WHERE data_id = %s AND location_id = %s LIMIT 1"
        data = (int(data_id), int(location_id))
        cur.execute(query, data)

        data_tupe = cur.fetchall()[0]
        cur.close()
        db.close()

        # Format data as parameter-value pairs for the template
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
        # Handle any errors that occur during data retrieval
        session["error_massage"] = "API abuse or SQL erro please contact the admins"
        return redirect("/apology")

    # Render the view template with location and parameter data
    return render_template("view.html", location_data=location_data, parameter_data=parameter_data, date=date, data_id=data_tupe[0])


# -------------------------------------------------------------------------
# DATA COMPARISON ROUTES
# -------------------------------------------------------------------------

@data_bp.route("/compare_between_data", methods=["GET", "POST"])
def compare_between():
    """
    Allows comparison between two data entries for the same location.
    GET: Displays form to select entries to compare.
    POST: Shows comparison in either table or graph format.
    """
    if request.method == "GET":
        # Get location ID from session
        location_id = session.get("location_id")

        # Use context manager to ensure connections are closed
        try:
            with DatabaseConnection() as (cur, db):
                query = "SELECT * FROM data WHERE location_id = %s ORDER BY date_submitted DESC"
                data = (int(location_id), )
                cur.execute(query, data)
                data_list = cur.fetchall()
        except Exception as e:
            session["error_massage"] = f"Error retrieving data: {str(e)}"
            return redirect(url_for("auth.apology"))

        # Display form to select which data entries to compare
        return render_template("compare_between.html", data_list=data_list)
    
    if request.method == "POST":
        # Process form submission for data comparison
        
        # Get form data
        location_id = session.get("location_id")
        data_id_1 = request.form.get("data_id_1")
        data_id_2 = request.form.get("data_id_2")
        compare_in = request.form.get("compare_in")  # Table or graph format

        try:
            # Get location and data in a more robust manner with exception handling
            with DatabaseConnection() as (cur, db):
                # Get location information
                query = "SELECT * FROM locations WHERE location_id = %s"
                data = (int(location_id), )
                cur.execute(query, data)
                location_data_tuple = cur.fetchall()[0]
                
                # Format location data for the template
                location_data = {
                    "location_id": location_data_tuple[0],
                    "location_name": location_data_tuple[2],
                    "description": location_data_tuple[3]
                }
                
                # Get both data entries in a single connection
                query1 = "SELECT * FROM data WHERE data_id = %s"
                query2 = "SELECT * FROM data WHERE data_id = %s"
                
                cur.execute(query1, (int(data_id_1),))
                data_tupe = cur.fetchall()[0]
                
                cur.execute(query2, (int(data_id_2),))
                data_tupe_2 = cur.fetchall()[0]
                
                # Get dates for both entries
                date = [data_tupe[3], data_tupe_2[3]]
        except Exception as e:
            session["error_massage"] = f"Error retrieving data: {str(e)}"
            return redirect(url_for("auth.apology"))
        
        # Process data based on selected comparison type
        if compare_in == "table":
            # Format data for table comparison (side-by-side)
            # Fix unit labels for consistency
            parameter_data = [
            ("Ph", data_tupe[4], data_tupe_2[4]),
            ("BOD (mg/l)", data_tupe[5], data_tupe_2[5]),
            ("COD (mg/l)", data_tupe[6], data_tupe_2[6]),
            ("Temperature (ᵒC)", data_tupe[7], data_tupe_2[7]),
            ("Ammonia (mg/l)", data_tupe[8], data_tupe_2[8]),
            ("Arsenic (mg/l)", data_tupe[9], data_tupe_2[9]),
            ("Calcium (mg/l)", data_tupe[10], data_tupe_2[10]),
            ("EC (µS/cm)", data_tupe[11], data_tupe_2[11]),
            ("Coliform (Faecal) (N/100ml)", data_tupe[12], data_tupe_2[12]),
            ("Hardness (mg/l)", data_tupe[13], data_tupe_2[13]),
            ("Lead (mg/l)", data_tupe[14], data_tupe_2[14]),
            ("Nitrogen (mg/l)", data_tupe[15], data_tupe_2[15]),
            ("Sodium (mg/l)", data_tupe[16], data_tupe_2[16]),
            ("Sulfate (mg/l)", data_tupe[17], data_tupe_2[17]),
            ("TSS (mg/l)", data_tupe[18], data_tupe_2[18]),
            ("Turbidity (NTU)", data_tupe[19], data_tupe_2[19]),
            ("TDS (mg/l)", data_tupe[20], data_tupe_2[20])
            ]

            # Render table comparison view
            return render_template("table_compare.html", location_data=location_data, parameter_data=parameter_data, date=date)
            
        if compare_in == "graph":
            # Format data for graphical comparison
            # Create dictionaries for each dataset to be used by JavaScript charts
            location_1_data = {
            "ph": data_tupe[4],
            "bod": data_tupe[5],
            "cod": data_tupe[6],
            "temperature": data_tupe[7], 
            "ammonia": data_tupe[8],
            "arsenic": data_tupe[9],
            "calcium": data_tupe[10],
            "ec": data_tupe[11],
            "coliform": data_tupe[12],
            "hardness": data_tupe[13],
            "lead_pb": data_tupe[14],
            "nitrogen": data_tupe[15],
            "sodium": data_tupe[16],
            "sulfate": data_tupe[17],
            "tss": data_tupe[18],
            "turbidity": data_tupe[19],
            "tds": data_tupe[20]
            }

            location_2_data = {
            "ph": data_tupe_2[4],
            "bod": data_tupe_2[5],
            "cod": data_tupe_2[6],
            "temperature": data_tupe_2[7], 
            "ammonia": data_tupe_2[8],
            "arsenic": data_tupe_2[9],
            "calcium": data_tupe_2[10],
            "ec": data_tupe_2[11],
            "coliform": data_tupe_2[12],
            "hardness": data_tupe_2[13],
            "lead_pb": data_tupe_2[14],
            "nitrogen": data_tupe_2[15],
            "sodium": data_tupe_2[16],
            "sulfate": data_tupe_2[17],
            "tss": data_tupe_2[18],
            "turbidity": data_tupe_2[19],
            "tds": data_tupe_2[20]
            }

            date_dic = {
                "left": date[0],
                "right": date[1]
            }

            # Render graph comparison view
            return render_template("graph_compare.html", location_1_data=location_1_data, location_2_data=location_2_data, date_dic=date_dic, location_data=location_data)


@data_bp.route("/compare_between_locations", methods=["GET", "POST"])
def compare_between_locations():
    """
    Allows comparison between data entries from different locations.
    GET: Displays form to select locations to compare.
    POST: Shows comparison in either table or graph format.
    """
    if request.method == "GET":
        # Getting all the location that have at least 1 data submitted to them 
        try:
            with DatabaseConnection() as (cur, db):
                query = "SELECT location_id, location_name FROM locations WHERE location_id IN (SELECT location_id FROM data) ORDER BY location_name"
                cur.execute(query)
                locations_tuple_liist = cur.fetchall()
        except Exception as e:
            session["error_massage"] = f"Error retrieving locations: {str(e)}"
            return redirect(url_for("auth.apology"))

        locations_dict_list = []
        for tuple in locations_tuple_liist:
            locations_dict_list.append({
                "location_id": tuple[0],
                "location_name": tuple[1]
            })

        return render_template("compare_between_locations.html", locations=locations_dict_list)
    
    if request.method == "POST":
        location_id_1 = request.form.get("location_id_1")
        location_id_2 = request.form.get("location_id_2")

        if location_id_1 == location_id_2:
            session["error_massage"] = "You have selected the same location to compare, please select diffrent locations"
            return redirect(url_for("auth.apology"))

        try:
            with DatabaseConnection() as (cur, db):
                # Get location names
                query = "SELECT location_name FROM locations WHERE location_id IN (%s, %s)"
                data = (int(location_id_1), int(location_id_2))
                cur.execute(query, data)
                locations_list_tupe = cur.fetchall()
                
                location_data = {
                    "location_name_1": locations_list_tupe[0][0],
                    "location_name_2": locations_list_tupe[1][0]
                }

                compare_in = request.form.get("compare_in")
                
                # Get data for both locations in a single connection
                query = "SELECT * FROM data WHERE location_id = %s ORDER BY date_submitted DESC LIMIT 1"
                
                # Get data for location 1
                cur.execute(query, (int(location_id_1),))
                data_tupe = cur.fetchall()[0]
                
                # Get data for location 2
                cur.execute(query, (int(location_id_2),))
                data_tupe_2 = cur.fetchall()[0]
        except Exception as e:
            session["error_massage"] = f"Error retrieving location data: {str(e)}"
            return redirect(url_for("auth.apology"))

        if compare_in == "table":   
            # Making a list of data parameters tuple to be used in the HTML table
            # Fix unit labels for consistency
            parameter_data = [
            ("Ph", data_tupe[4], data_tupe_2[4]),
            ("BOD (mg/l)", data_tupe[5], data_tupe_2[5]),
            ("COD (mg/l)", data_tupe[6], data_tupe_2[6]),
            ("Temperature (ᵒC)", data_tupe[7], data_tupe_2[7]),
            ("Ammonia (mg/l)", data_tupe[8], data_tupe_2[8]),
            ("Arsenic (mg/l)", data_tupe[9], data_tupe_2[9]),
            ("Calcium (mg/l)", data_tupe[10], data_tupe_2[10]),
            ("EC (µS/cm)", data_tupe[11], data_tupe_2[11]),
            ("Coliform (Faecal) (N/100ml)", data_tupe[12], data_tupe_2[12]),
            ("Hardness (mg/l)", data_tupe[13], data_tupe_2[13]),
            ("Lead (mg/l)", data_tupe[14], data_tupe_2[14]),
            ("Nitrogen (mg/l)", data_tupe[15], data_tupe_2[15]),
            ("Sodium (mg/l)", data_tupe[16], data_tupe_2[16]),
            ("Sulfate (mg/l)", data_tupe[17], data_tupe_2[17]),
            ("TSS (mg/l)", data_tupe[18], data_tupe_2[18]),
            ("Turbidity (NTU)", data_tupe[19], data_tupe_2[19]),
            ("TDS (mg/l)", data_tupe[20], data_tupe_2[20])
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
            "ammonia": data_tupe[8],
            "arsenic": data_tupe[9],
            "calcium": data_tupe[10],
            "ec": data_tupe[11],
            "coliform": data_tupe[12],
            "hardness": data_tupe[13],
            "lead_pb": data_tupe[14],
            "nitrogen": data_tupe[15],
            "sodium": data_tupe[16],
            "sulfate": data_tupe[17],
            "tss": data_tupe[18],
            "turbidity": data_tupe[19],
            "tds": data_tupe[20]
            }

            location_2_data = {
            "ph": data_tupe_2[4],
            "bod": data_tupe_2[5],
            "cod": data_tupe_2[6],
            "temperature": data_tupe_2[7], 
            "ammonia": data_tupe_2[8],
            "arsenic": data_tupe_2[9],
            "calcium": data_tupe_2[10],
            "ec": data_tupe_2[11],
            "coliform": data_tupe_2[12],
            "hardness": data_tupe_2[13],
            "lead_pb": data_tupe_2[14],
            "nitrogen": data_tupe_2[15],
            "sodium": data_tupe_2[16],
            "sulfate": data_tupe_2[17],
            "tss": data_tupe_2[18],
            "turbidity": data_tupe_2[19],
            "tds": data_tupe_2[20]
            }

            return render_template("compare_between_locations_graph.html", location_data=location_data, location_1_data=location_1_data, location_2_data=location_2_data)


@data_bp.route("/analyze_water/<int:data_id>")
def analyze_water(data_id):
    """
    Analyzes water quality data and displays results.
    Uses the water_quality utility to generate analysis.
    """
    if not session.get("user_id"):
        return redirect("/login")
    
    try:
        with DatabaseConnection(dictionary=True) as (cur, db):
            # Get data parameters
            query = "SELECT * FROM data WHERE data_id = %s"
            data = (data_id, )
            cur.execute(query, data)
            
            if cur.rowcount == 0:
                session["error_massage"] = "Data not found"
                return redirect(url_for("auth.apology"))
            
            water_data = cur.fetchone()
            
            # Get location information
            location_id = water_data["location_id"]
            query = "SELECT * FROM locations WHERE location_id = %s"
            data = (location_id, )
            cur.execute(query, data)
            location = cur.fetchone()
    except Exception as e:
        session["error_massage"] = f"Error retrieving data for analysis: {str(e)}"
        return redirect(url_for("auth.apology"))
    
    # Analyze water quality
    analysis_result = analyze_water_quality(water_data)
    
    return render_template(
        "analyze_water.html", 
        water_data=water_data, 
        location=location, 
        analysis=analysis_result
    )

@data_bp.route("/download_report/<int:data_id>")
def download_report(data_id):
    """
    Generates and downloads a PDF report of water quality analysis.
    """
    if not session.get("user_id"):
        return redirect("/login")
    
    try:
        with DatabaseConnection(dictionary=True) as (cur, db):
            # Get data parameters
            query = "SELECT * FROM data WHERE data_id = %s"
            data = (data_id, )
            cur.execute(query, data)
            
            if cur.rowcount == 0:
                session["error_massage"] = "Data not found"
                return redirect(url_for("auth.apology"))
            
            water_data = cur.fetchone()
            
            # Get location information
            location_id = water_data["location_id"]
            query = "SELECT * FROM locations WHERE location_id = %s"
            data = (location_id, )
            cur.execute(query, data)
            location = cur.fetchone()
        
        # Analyze water quality
        analysis_result = analyze_water_quality(water_data)
        
        # Generate PDF report
        pdf_path = generate_water_quality_report(location, water_data, analysis_result)
        
        if not pdf_path or not os.path.exists(pdf_path):
            session["error_massage"] = "Error generating PDF report. Please try again later."
            return redirect(url_for("auth.apology"))
        
        # Create a filename for the download
        safe_name = ''.join(c if c.isalnum() else '_' for c in location['location_name'])
        filename = f"water_quality_report_{safe_name}_{data_id}.pdf"
        
        # Send the file to the user
        try:
            return send_file(
                pdf_path,
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf'
            )
        except Exception as e:
            print(f"Error sending file: {e}")
            session["error_massage"] = "Error sending PDF report. Please try again later."
            return redirect(url_for("auth.apology"))
        finally:
            # Clean up the temporary file after sending
            if os.path.exists(pdf_path):
                try:
                    os.unlink(pdf_path)
                except:
                    pass
    
    except Exception as e:
        print(f"Error in download_report: {e}")
        session["error_massage"] = f"An error occurred while generating the report: {str(e)}"
        return redirect(url_for("auth.apology"))

@data_bp.route("/gauge_visualization/<int:data_id>")
def gauge_visualization(data_id):
    """
    Displays gauge chart visualizations for key water quality parameters.
    """
    if not session.get("user_id"):
        return redirect("/login")
    
    try:
        with DatabaseConnection(dictionary=True) as (cur, db):
            # Get data parameters
            query = "SELECT * FROM data WHERE data_id = %s"
            data = (data_id, )
            cur.execute(query, data)
            
            if cur.rowcount == 0:
                session["error_massage"] = "Data not found"
                return redirect(url_for("auth.apology"))
            
            water_data = cur.fetchone()
            
            # Get location information
            location_id = water_data["location_id"]
            query = "SELECT * FROM locations WHERE location_id = %s"
            data = (location_id, )
            cur.execute(query, data)
            location = cur.fetchone()
    except Exception as e:
        session["error_massage"] = f"Error retrieving data for visualization: {str(e)}"
        return redirect(url_for("auth.apology"))
    
    # Define acceptable ranges for parameters
    # These values should be aligned with your water quality analysis function
    acceptable_ranges = {
        "ph": {"min": 6.5, "max": 8.5, "label": "pH"},
        "bod": {"min": 0, "max": 6, "label": "BOD (mg/l)"},
        "cod": {"min": 0, "max": 10, "label": "COD (mg/l)"},
        "temperature": {"min": 20, "max": 30, "label": "Temperature (°C)"},
        "turbidity": {"min": 0, "max": 5, "label": "Turbidity (NTU)"},
        "tds": {"min": 0, "max": 500, "label": "TDS (mg/l)"},
        "ec": {"min": 0, "max": 800, "label": "EC (μS/cm)"}
        # Add other parameters as needed
    }
    
    # Pass only parameters that have values in the water_data
    gauge_data = {}
    for param, range_info in acceptable_ranges.items():
        if water_data[param] is not None:
            gauge_data[param] = {
                "value": float(water_data[param]),
                "min": range_info["min"],
                "max": range_info["max"],
                "label": range_info["label"]
            }
    
    return render_template(
        "gauge_charts.html", 
        water_data=water_data, 
        location=location, 
        gauge_data=gauge_data
    ) 