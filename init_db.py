import sqlite3
import os
from config import DB_CONFIG

def init_db():
    """Initialize the SQLite database from schema file"""
    db_path = DB_CONFIG["database"]
    
    # Check if database already exists and remove it for a clean start
    if os.path.exists(db_path):
        print(f"Removing existing database: {db_path}")
        os.remove(db_path)
    
    print(f"Creating new SQLite database: {db_path}")
    
    # Connect to SQLite database (will create it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    
    try:
        # Read the schema file
        with open('SQL/sqlite_schema.sql', 'r') as f:
            schema = f.read()
        
        # Execute the schema script
        conn.executescript(schema)
        conn.commit()
        print("Database schema created successfully!")
        
    except sqlite3.Error as e:
        print(f"Error creating database schema: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    print("SQLite database initialization complete.") 