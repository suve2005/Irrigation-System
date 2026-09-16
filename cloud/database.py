# database.py
import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "SUVEthican2005",
    "database": "irrigation_system"
}

def get_db_connection():
    """Returns a fresh connection to the MySQL database."""
    return mysql.connector.connect(**DB_CONFIG)