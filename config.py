import os

# Database configuration
DB_CONFIG = {
    "database": "water.db"  # SQLite database file
}

# App configuration
SECRET_KEY = "development_secret_key_h20insight"  # Fixed key for development
SESSION_TYPE = "filesystem"
SESSION_PERMANENT = False 