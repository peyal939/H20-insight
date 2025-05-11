from flask import Blueprint, request, render_template, session, redirect, url_for, flash, jsonify
from werkzeug.security import generate_password_hash
from decimal import Decimal
from models.db import get_cursor, DatabaseConnection, has_rows
import os
import datetime
from functools import wraps

# Create admin blueprint - This registers all admin routes with Flask
admin_bp = Blueprint('admin', __name__)

# Admin access decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_type") != "A":
            session["error_message"] = "This page is only for admins."
            return redirect(url_for("auth.apology"))
        return f(*args, **kwargs)
    return decorated_function

# -------------------------------------------------------------------------
# ADMIN DASHBOARD ROUTES
# -------------------------------------------------------------------------

@admin_bp.route("/admin")
@admin_required
def admin():
    """
    Admin dashboard that displays system statistics.
    Access restricted to admin users only.
    Shows counts of users, locations, and measurements.
    """
    # Get statistics for admin dashboard
    cur, db = get_cursor()
    
    # Get user count
    cur.execute("SELECT COUNT(*) FROM users")
    user_count = cur.fetchone()[0]
    
    # Get location count
    cur.execute("SELECT COUNT(*) FROM locations")
    location_count = cur.fetchone()[0]
    
    # Get measurement count
    cur.execute("SELECT COUNT(*) FROM data")
    measurement_count = cur.fetchone()[0]
    
    cur.close()
    db.close()
    
    # Create stats dictionary to pass to template
    stats = {
        "user_count": user_count,
        "location_count": location_count,
        "measurement_count": measurement_count
    }
    
    return render_template("admin.html", stats=stats)


# -------------------------------------------------------------------------
# USER MANAGEMENT ROUTES
# -------------------------------------------------------------------------

@admin_bp.route("/admin_users")
@admin_required
def admin_users():
    """
    Displays a list of all non-admin users in the system.
    Only accessible to administrators.
    """
    # Gets all users excluding admins
    cur, db = get_cursor()
    cur.execute("SELECT user_id, user_name, user_type FROM users WHERE user_type != 'A'")
    users = cur.fetchall()
    cur.close()
    db.close()
    
    return render_template("admin_user.html", users=users)


@admin_bp.route("/admin_user_edit", methods=["GET", "POST"])
@admin_required
def admin_user_edit():
    """
    Allows administrators to edit user information.
    GET: Displays a form with the user's current information.
    POST: Processes form submission and updates user data.
    """
    # Get user_id from either URL parameter (GET) or form data (POST)
    user_id = request.args.get("user_id") if request.method == "GET" else request.form.get("user_id")
    
    # Validate user_id is provided
    if not user_id:
        session["error_message"] = "No user ID provided."
        return redirect(url_for("auth.apology"))

    if request.method == "GET":
        # Display user edit form
        
        # Check if there's a success message in the session
        success_message = None
        if session.get("success_message"):
            success_message = session.get("success_message")
            session.pop("success_message")
            
        cur, db = get_cursor()
        try:
            # Get user data from database
            cur.execute("SELECT user_name, email, latitude, longitude, first_name, last_name, user_type FROM users WHERE user_id = ?", (int(user_id), ))
            result = cur.fetchall()
            
            # Check if any result was returned
            if not result:
                session["error_message"] = f"No user found with ID {user_id}."
                cur.close()
                db.close()
                return redirect(url_for("auth.apology"))
                
            user_data = result[0]
            cur.close()
            db.close()
        except ValueError:
            # Handle cases where user_id is not a valid integer
            session["error_message"] = "Invalid user ID format."
            cur.close()
            db.close()
            return redirect(url_for("auth.apology"))

        return render_template("admin_user_edit.html", user_data=user_data, user_id=user_id, success_message=success_message)
    
    if request.method == "POST":
        # Process form submission to update user data
        
        # Get form data
        user_name = request.form.get("user_name")
        email = request.form.get("email")
        password = request.form.get("password")
        password_again = request.form.get("password_again")
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        user_type = request.form.get("user_type")

        # Track if any changes were made
        changes_made = False

        # Get current user data first to compare what's being changed
        cur, db = get_cursor()
        cur.execute("SELECT user_name, email FROM users WHERE user_id = ?", (user_id, ))
        current_user = cur.fetchone()
        
        # Check if user exists
        if not current_user:
            session["error_message"] = f"No user found with ID {user_id}."
            cur.close()
            db.close()
            return redirect(url_for("auth.apology"))
            
        current_username = current_user[0]
        current_email = current_user[1]
        cur.close()
        db.close()

        # Update username if changed and not taken by another user
        if user_name and user_name != current_username:
            # Check if username is taken by another user
            cur, db = get_cursor()
            cur.execute("SELECT * FROM users WHERE user_name = ? AND user_id != ?", (user_name, user_id))
            if cur.fetchone():
                cur.close()
                db.close()
                session["error_message"] = "Username already exists"
                return redirect(url_for("auth.apology"))
            else:
                cur.close()
                db.close()
                cur, db = get_cursor()
                cur.execute("UPDATE users SET user_name = ? WHERE user_id = ?", (user_name, user_id))
                db.commit()
                cur.close()
                db.close()
                changes_made = True

        # Update email if changed and not taken by another user
        if email and email != current_email:
            # Check if email is taken by another user
            cur, db = get_cursor()
            cur.execute("SELECT * FROM users WHERE email = ? AND user_id != ?", (email, user_id))
            if cur.fetchone():
                cur.close()
                db.close()
                session["error_message"] = "Email is already in use"
                return redirect(url_for("auth.apology"))
            else:
                cur.close()
                db.close()
                cur, db = get_cursor()
                cur.execute("UPDATE users SET email = ? WHERE user_id = ?", (email, user_id))
                db.commit()
                cur.close()
                db.close()
                changes_made = True

        # Update password if provided
        if password:
            # Validate password confirmation matches
            if password != password_again:
                session["error_message"] = "Confirmation dose not match"
                return redirect(url_for("auth.apology"))
            
            # Hash password and update in database
            cur, db = get_cursor()
            cur.execute("UPDATE users SET password_hash = ? WHERE user_id = ?", (generate_password_hash(password), user_id))
            db.commit()
            cur.close()
            db.close()
            changes_made = True

        # Update latitude if provided and valid
        if latitude is not None:
            if not (-90 <= float(latitude) <= 90):
                return jsonify({"success": False, "message": "Latitude must be between -90 and 90"})
            cur, db = get_cursor()
            cur.execute("UPDATE users SET latitude = ? WHERE user_id = ?", (float(latitude), user_id))
            db.commit()
            cur.close()
            db.close()
            changes_made = True
        
        # Update longitude if provided and valid
        if longitude is not None:
            if not (-180 <= float(longitude) <= 180):
                return jsonify({"success": False, "message": "Longitude must be between -180 and 180"})
            cur, db = get_cursor()
            cur.execute("UPDATE users SET longitude = ? WHERE user_id = ?", (float(longitude), user_id))
            db.commit()
            cur.close()
            db.close()
            changes_made = True

        # Update first name if provided
        if first_name:
            # Validate first name length
            if len(first_name) > 255:
                session["error_message"] = "First name must be less then 255 characters"
                return redirect(url_for("auth.apology"))
            
            cur, db = get_cursor()
            cur.execute("UPDATE users SET first_name = ? WHERE user_id = ?", (first_name, user_id))
            db.commit()
            cur.close()
            db.close()
            changes_made = True

        # Update last name if provided
        if last_name:
            # Validate last name length
            if len(last_name) > 255:
                session["error_message"] = "Last name must be less then 255 characters"
                return redirect(url_for("auth.apology"))
            
            cur, db = get_cursor()
            cur.execute("UPDATE users SET last_name = ? WHERE user_id = ?", (last_name, user_id))
            db.commit()
            cur.close()
            db.close()
            changes_made = True

        # Update user type if provided
        if user_type:
            # Validate user type is valid (Volunteer or Researcher)
            if user_type not in ["V", "R"]:
                session["error_message"] = "Invalid user type"
                return redirect(url_for("auth.apology"))
            
            cur, db = get_cursor()
            cur.execute("UPDATE users SET user_type = ? WHERE user_id = ?", (user_type, user_id))
            db.commit()
            cur.close()
            db.close()
            changes_made = True
        
        # Set success message if changes were made
        if changes_made:
            # Use both session and flash message
            session["success_message"] = "User updated successfully!"
            flash("User updated successfully!")
            
            # Redirect to admin_users page instead of back to the edit page
            return redirect(url_for("admin.admin_users"))
        else:
            # If no changes were made, redirect back to edit page
            return redirect(url_for("admin.admin_user_edit", user_id=user_id))


# -------------------------------------------------------------------------
# LOCATION MANAGEMENT ROUTES
# -------------------------------------------------------------------------

@admin_bp.route("/admin_locations")
@admin_required
def admin_locations():
    """
    Displays a list of all locations in the system.
    Shows location details including who created each location.
    Only accessible to administrators.
    """
    cur, db = get_cursor()
    # Join with users table to get creator information
    cur.execute("""
        SELECT l.location_id, l.location_name, l.date_submitted, l.latitude, l.longitude, 
               COALESCE(u.user_name, 'Unknown') as creator_name
        FROM locations l
        LEFT JOIN users u ON l.user_id = u.user_id
    """)
    locations = cur.fetchall()
    cur.close()
    db.close()
    
    # Format the locations with proper column names for the template
    formatted_locations = []
    for loc in locations:
        formatted_locations.append({
            "id": loc[0],
            "name": loc[1],
            "date_submitted": loc[2],
            "latitude": loc[3],
            "longitude": loc[4],
            "created_by": loc[5]  # Use actual creator name from database
        })
    
    return render_template("admin_location.html", locations=formatted_locations)


@admin_bp.route("/admin_location_edit", methods=["GET", "POST"])
@admin_required
def admin_location_edit():
    """
    Allows administrators to edit location information.
    GET: Displays a form with the location's current information.
    POST: Processes form submission and updates location data.
    """
    # Get location_id from either URL parameter (GET) or form data (POST)
    location_id = request.args.get("location_id") if request.method == "GET" else request.form.get("location_id")
    
    # Validate location_id is provided
    if not location_id:
        session["error_message"] = "No location ID provided."
        return redirect(url_for("auth.apology"))

    if request.method == "GET":
        # Display location edit form
        
        cur, db = get_cursor()
        cur.execute("SELECT location_name, description, latitude, longitude FROM locations WHERE location_id = ?", (location_id, ))
        result = cur.fetchall()
        
        # Check if any result was returned
        if not result:
            session["error_message"] = f"No location found with ID {location_id}."
            cur.close()
            db.close()
            return redirect(url_for("auth.apology"))
            
        location_data = result[0]
        cur.close()
        db.close()

        return render_template("admin_location_edit.html", location_data=location_data, location_id=location_id)
    
    if request.method == "POST":
        # Process form submission to update location data
        
        # Get form data
        location_id = request.form.get("location_id")
        location_name = request.form.get("location_name")
        description = request.form.get("description")
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")

        # Verify location exists before making changes
        cur, db = get_cursor()
        cur.execute("SELECT location_id FROM locations WHERE location_id = ?", (location_id, ))
        if not cur.fetchone():
            cur.close()
            db.close()
            session["error_message"] = f"No location found with ID {location_id}."
            return redirect(url_for("auth.apology"))
        cur.close()
        db.close()

        # Update location name if provided
        if location_name:
            # Validate location name length
            if len(location_name) > 255:
                session["error_message"] = "Location name must be less then 255 chracters"
                return redirect(url_for("auth.apology"))
            
            # Check if location name is already taken by another location
            cur, db = get_cursor()
            cur.execute("SELECT * FROM locations WHERE location_name = ? AND location_id != ?", (location_name, location_id))
            if cur.fetchone():
                cur.close()
                db.close()
                session["error_message"] = "Location name taken"
                return redirect(url_for("auth.apology"))
           
            # Update location name in database
            cur, db = get_cursor()
            cur.execute("UPDATE locations SET location_name = ? WHERE location_id = ?", (location_name, location_id))
            db.commit()
            cur.close()
            db.close()

        # Update description if provided
        if description:
            # Validate description length
            if len(description) > 6000:
                session["error_message"] = "Description must be less then 6000 chracters"
                return redirect(url_for("auth.apology"))
            
            # Update description in database
            cur, db = get_cursor()
            cur.execute("UPDATE locations SET description = ? WHERE location_id = ?", (description, location_id))
            db.commit()
            cur.close()
            db.close()

        # Update latitude if provided and valid
        if latitude is not None:
            if not (-90 <= float(latitude) <= 90):
                return jsonify({"success": False, "message": "Latitude must be between -90 and 90"})
            cur, db = get_cursor()
            cur.execute("UPDATE locations SET latitude = ? WHERE location_id = ?", (float(latitude), location_id))
            db.commit()
            cur.close()
            db.close()
        
        # Update longitude if provided and valid
        if longitude is not None:
            if not (-180 <= float(longitude) <= 180):
                return jsonify({"success": False, "message": "Longitude must be between -180 and 180"})
            cur, db = get_cursor()
            cur.execute("UPDATE locations SET longitude = ? WHERE location_id = ?", (float(longitude), location_id))
            db.commit()
            cur.close()
            db.close()

        return redirect(url_for("admin.admin_location_edit", location_id=location_id))


# -------------------------------------------------------------------------
# DELETE OPERATIONS
# -------------------------------------------------------------------------

@admin_bp.route("/delete_user", methods=["POST"])
@admin_required
def delete_user():
    """
    Deletes a user from the system.
    Only accessible to administrators.
    Requires a valid user_id in the form data.
    """
    user_id = request.form.get("user_id")
    
    # Validate user_id is provided
    if not user_id:
        session["error_message"] = "No user ID provided."
        return redirect(url_for("auth.apology"))
        
    try:
        cur, db = get_cursor()
        # Check if user exists
        cur.execute("SELECT user_id FROM users WHERE user_id = ?", (int(user_id), ))
        if not cur.fetchone():
            cur.close()
            db.close()
            session["error_message"] = f"No user found with ID {user_id}."
            return redirect(url_for("auth.apology"))
            
        # Delete user from database
        cur.execute("DELETE FROM users WHERE user_id = ?", (int(user_id), ))
        db.commit()
        cur.close()
        db.close()

        return redirect(url_for("admin.admin_users"))
    except ValueError:
        # Handle cases where user_id is not a valid integer
        session["error_message"] = "Invalid user ID format."
        return redirect(url_for("auth.apology"))
    

@admin_bp.route("/delete_location", methods=["POST"])
@admin_required
def delete_location():
    """
    Deletes a location from the system.
    Only accessible to administrators.
    Requires a valid location_id in the form data.
    """
    location_id = request.form.get("location_id")
    
    # Validate location_id is provided
    if not location_id:
        session["error_message"] = "No location ID provided."
        return redirect(url_for("auth.apology"))
        
    try:
        cur, db = get_cursor()
        # Check if location exists
        cur.execute("SELECT location_id FROM locations WHERE location_id = ?", (int(location_id), ))
        if not cur.fetchone():
            cur.close()
            db.close()
            session["error_message"] = f"No location found with ID {location_id}."
            return redirect(url_for("auth.apology"))
            
        # Delete location from database
        cur.execute("DELETE FROM locations WHERE location_id = ?", (int(location_id), ))
        db.commit()
        cur.close()
        db.close()

        return redirect(url_for("admin.admin_locations"))
    except ValueError:
        # Handle cases where location_id is not a valid integer
        session["error_message"] = "Invalid location ID format."
        return redirect(url_for("auth.apology"))
    

@admin_bp.route("/delete_data", methods=["POST"])
@admin_required
def delete_data():
    """
    Deletes a water quality data entry from the system.
    Only accessible to administrators.
    Requires valid data_id and location_id in the form data.
    """
    data_id = request.form.get("data_id")
    location_id = request.form.get("location_id")
    
    # Validate data_id and location_id are provided
    if not data_id or not location_id:
        session["error_message"] = "Data ID or Location ID not provided."
        return redirect(url_for("auth.apology"))
        
    try:
        cur, db = get_cursor()
        # Check if data exists
        cur.execute("SELECT data_id FROM data WHERE data_id = ?", (int(data_id), ))
        if not cur.fetchone():
            cur.close()
            db.close()
            session["error_message"] = f"No data found with ID {data_id}."
            return redirect(url_for("auth.apology"))
            
        # Check if location exists
        cur.execute("SELECT location_id FROM locations WHERE location_id = ?", (int(location_id), ))
        if not cur.fetchone():
            cur.close()
            db.close()
            session["error_message"] = f"No location found with ID {location_id}."
            return redirect(url_for("auth.apology"))
            
        # Delete data from database
        cur.execute("DELETE FROM data WHERE data_id = ?", (int(data_id), ))
        db.commit()
        cur.close()
        db.close()

        # Redirect back to location view page
        return redirect(url_for("locations.view", location_id=location_id))
    except ValueError:
        # Handle cases where data_id or location_id is not a valid integer
        session["error_message"] = "Invalid ID format."
        return redirect(url_for("auth.apology")) 