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
    """
    Check if the cursor result has any rows
    
    Note: This will consume the first row of the result set.
    After calling this function, you should re-execute your query
    if you need the complete result set.
    
    Usage pattern:
    
    cur.execute("SELECT * FROM table WHERE condition = ?", (value,))
    if has_rows(cur):
        # Re-execute the query to get all results
        cur.execute("SELECT * FROM table WHERE condition = ?", (value,))
        results = cur.fetchall()
        # Process results...
    else:
        # No rows found
        pass
    """
    # The simplest and most reliable approach for SQLite
    # Just check if fetchone() returns a row
    row = cursor.fetchone()
    return row is not None

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