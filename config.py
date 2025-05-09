import os

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "4044",
    "database": "water"
}

# App configuration
SECRET_KEY = "development_secret_key_h20insight"  # Fixed key for development
SESSION_TYPE = "filesystem"
SESSION_PERMANENT = False 