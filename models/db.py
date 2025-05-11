import sqlite3
from config import DB_CONFIG
import sys
import os

# Ensure the database file exists
DB_PATH = DB_CONFIG["database"]

# Create a database connection
def get_db_connection():
    try:
        connection = sqlite3.connect(DB_PATH)
        # Enable foreign keys
        connection.execute("PRAGMA foreign_keys = ON")
        # Return dictionary-like objects for rows
        connection.row_factory = sqlite3.Row
        return connection
    except sqlite3.Error as err:
        print(f"Database connection error: {err}", file=sys.stderr)
        raise

# Function to check if a result set has rows (replacement for cur.rowcount check)
def has_rows(cursor):
    """Check if the cursor result has any rows"""
    row = cursor.fetchone()
    if row:
        # Reset cursor by re-executing the last query
        cursor.execute(cursor.statement, cursor.getconnection().last_execute_params or ())
        return True
    return False

# Get a cursor for database operations
def get_cursor(dictionary=False):
    """Get a database cursor and connection"""
    db = sqlite3.connect(DB_PATH)
    # Enable foreign keys
    db.execute("PRAGMA foreign_keys = ON")
    
    if dictionary:
        db.row_factory = sqlite3.Row
    
    cur = db.cursor()
    
    return cur, db

class DatabaseConnection:
    """Context manager for database connections to ensure proper cleanup"""
    def __init__(self, dictionary=False):
        self.dictionary = dictionary
        self.cursor = None
        self.connection = None
        
    def __enter__(self):
        """Open the database connection when entering the context"""
        self.connection = sqlite3.connect(DB_PATH)
        # Enable foreign keys
        self.connection.execute("PRAGMA foreign_keys = ON")
        
        if self.dictionary:
            self.connection.row_factory = sqlite3.Row
            
        self.cursor = self.connection.cursor()
        return self.cursor, self.connection
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure connection is properly closed when exiting the context"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        return False  # Let any exceptions propagate 