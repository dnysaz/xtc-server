import sqlite3
import os

DB_NAME = "xtc.db"

def get_db_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_tables():
    """Initializes the required tables and schema for XTC-CLI."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Table to store chat messages
    cursor.execute('''CREATE TABLE IF NOT EXISTS messages 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       room TEXT, 
                       sender TEXT, 
                       content TEXT)''')
    
    # Menambahkan kolom timestamp ke tabel messages jika belum ada
    try:
        cursor.execute("ALTER TABLE messages ADD COLUMN timestamp TEXT")
    except sqlite3.OperationalError:
        pass

    # Table to manage rooms and ownership
    cursor.execute('''CREATE TABLE IF NOT EXISTS rooms 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       name TEXT UNIQUE, 
                       creator TEXT)''')
    
    # Menambahkan kolom password jika belum ada
    try:
        cursor.execute("ALTER TABLE rooms ADD COLUMN password TEXT")
    except sqlite3.OperationalError:
        pass
    
    conn.commit()
    conn.close()

# Memastikan tabel selalu terupdate saat aplikasi dijalankan
if __name__ == '__main__':
    init_tables()
else:
    init_tables()