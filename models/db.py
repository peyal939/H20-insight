import mysql.connector
from config import DB_CONFIG
import sys

# Create a database connection
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"]
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}", file=sys.stderr)
        raise

# Get a cursor for database operations
def get_cursor(dictionary=False):
    """Get a database cursor and connection"""
    db = mysql.connector.connect(**DB_CONFIG)
    cur = db.cursor(buffered=True, dictionary=dictionary)
    return cur, db

class DatabaseConnection:
    """Context manager for database connections to ensure proper cleanup"""
    def __init__(self, dictionary=False):
        self.dictionary = dictionary
        self.cursor = None
        self.connection = None
        
    def __enter__(self):
        """Open the database connection when entering the context"""
        self.connection = mysql.connector.connect(**DB_CONFIG)
        self.cursor = self.connection.cursor(buffered=True, dictionary=self.dictionary)
        return self.cursor, self.connection
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure connection is properly closed when exiting the context"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        return False  # Let any exceptions propagate 