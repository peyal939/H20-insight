from flask import Flask, render_template, request, session, redirect
from flask_session import Session
from config import SECRET_KEY, SESSION_TYPE, SESSION_PERMANENT
from datetime import datetime

# Import blueprints
from routes.auth import auth_bp
from routes.locations import locations_bp
from routes.data import data_bp
from routes.profile import profile_bp
from routes.support import support_bp
from routes.admin import admin_bp

# App config
app = Flask(__name__)
app.secret_key = SECRET_KEY

# Session config 
app.config["SESSION_PERMANENT"] = SESSION_PERMANENT
app.config["SESSION_TYPE"] = SESSION_TYPE
Session(app)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(locations_bp)
app.register_blueprint(data_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(support_bp)
app.register_blueprint(admin_bp)

# landing page and search
@app.route("/", methods=["GET", "POST"])
def index():
    from models.db import get_cursor

    if request.method == "GET":
        if session.get("user_id"):      
            # Get statistics for the dashboard
            cur, db = get_cursor()
            
            # Count total locations
            cur.execute("SELECT COUNT(*) FROM locations")
            location_count = cur.fetchone()[0]
            
            # Count total measurements
            cur.execute("SELECT COUNT(*) FROM data")
            measurement_count = cur.fetchone()[0]
            
            # Count researchers
            cur.execute("SELECT COUNT(*) FROM users WHERE user_type = 'R'")
            researcher_count = cur.fetchone()[0]
            
            # Get recent locations
            cur.execute("SELECT location_id, location_name, date_submitted FROM locations ORDER BY date_submitted DESC LIMIT 5")
            recent_locations_raw = cur.fetchall()
            
            # Format recent locations for template
            recent_locations = []
            for loc in recent_locations_raw:
                recent_locations.append({
                    "location_id": loc[0],
                    "location_name": loc[1],
                    "date_submitted": loc[2]
                })
            
            cur.close()
            db.close()
            
            return render_template(
                "index.html", 
                location_count=location_count,
                measurement_count=measurement_count,
                researcher_count=researcher_count,
                recent_locations=recent_locations,
                current_time=datetime.now().strftime('%Y-%m-%d %H:%M')
            )
        
        else:
            # Show landing page for non-logged-in users
            return render_template("index.html", current_time=datetime.now().strftime('%Y-%m-%d %H:%M'))
        
    if request.method == "POST":
        q = request.form.get("q")

        cur, db = get_cursor()
        query = "SELECT * FROM locations WHERE location_name LIKE ?"
        data = ("%" + str(q) + "%", )
        cur.execute(query, data) 
        search_result = cur.fetchall()

        cur.close()
        db.close()

        return render_template("search.html", search_result=search_result, q=str(q))


# Add this at the end of the file
if __name__ == "__main__":
    app.run(debug=True)
    