import sqlite3
import os

DB_NAME = "xtc.db"

def get_db_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_tables():
    """Initializes the required tables and schema for XtermChat."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Tabel Users (Identity Lock)
    # Menyimpan PIN untuk setiap handle/nama unik
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (username TEXT PRIMARY KEY, 
                       pin TEXT NOT NULL)''')
    
    # 2. Tabel Messages
    # Menambahkan kolom 'pin' untuk memverifikasi kepemilikan bubble chat
    cursor.execute('''CREATE TABLE IF NOT EXISTS messages 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       room TEXT, 
                       sender TEXT, 
                       pin TEXT,
                       content TEXT,
                       timestamp TEXT DEFAULT (datetime('now', 'localtime')))''')
    
    # Migrasi Kolom (Failsafe jika DB sudah ada)
    try:
        cursor.execute("ALTER TABLE messages ADD COLUMN pin TEXT")
    except sqlite3.OperationalError:
        pass # Column already exists English: pin column added
    
    try:
        cursor.execute("ALTER TABLE messages ADD COLUMN timestamp TEXT DEFAULT (datetime('now', 'localtime'))")
    except sqlite3.OperationalError:
        pass # Column already exists English: timestamp column added

    # 3. Tabel Rooms
    cursor.execute('''CREATE TABLE IF NOT EXISTS rooms 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                   name TEXT UNIQUE, 
                   creator TEXT,
                   password TEXT,
                   description TEXT,
                   created_at INTEGER)''')
    
    # Migrasi Kolom Password
    try:
        cursor.execute("ALTER TABLE rooms ADD COLUMN password TEXT")
    except sqlite3.OperationalError:
        pass # Column already exists English: password column added
    
    conn.commit()
    conn.close()

# Inisialisasi otomatis saat module diimport
init_tables()