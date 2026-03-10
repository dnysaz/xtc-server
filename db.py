import sqlite3
import os

DB_NAME = "xtc.db"

def get_db_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    # Enable row factory for easier data access
    conn.row_factory = sqlite3.Row
    return conn

def init_tables():
    """Initializes the required tables for XTC-CLI."""
    conn = get_db_connection()
    
    # Table to store chat messages
    conn.execute('''CREATE TABLE IF NOT EXISTS messages 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                     room TEXT, 
                     sender TEXT, 
                     content TEXT)''')
    
    # Table to manage rooms and ownership
    conn.execute('''CREATE TABLE IF NOT EXISTS rooms 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                     name TEXT UNIQUE, 
                     creator TEXT)''')
    
    conn.commit()
    conn.close()

# Helper for debugging: Ensure DB exists or handle errors
if not os.path.exists(DB_NAME):
    init_tables()