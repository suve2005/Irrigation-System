# database.py
import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "YOUR_PASSWORD_HERE", # Change this
    "database": "irrigation_db"
}

def get_db_connection():
    """Returns a fresh connection to the MySQL database."""
    return mysql.connector.connect(**DB_CONFIG)