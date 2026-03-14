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
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (username TEXT PRIMARY KEY, 
                       pin TEXT NOT NULL)''')

    # 2. Tabel Messages
    cursor.execute('''CREATE TABLE IF NOT EXISTS messages 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       room TEXT, 
                       sender TEXT, 
                       pin TEXT,
                       content TEXT,
                       timestamp TEXT DEFAULT (datetime('now', 'localtime')))''')

    # Migrasi kolom messages (failsafe jika DB sudah ada)
    try:
        cursor.execute("ALTER TABLE messages ADD COLUMN pin TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE messages ADD COLUMN timestamp TEXT DEFAULT (datetime('now', 'localtime'))")
    except sqlite3.OperationalError:
        pass

    # 3. Tabel Rooms
    cursor.execute('''CREATE TABLE IF NOT EXISTS rooms 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       name TEXT UNIQUE, 
                       creator TEXT,
                       password TEXT,
                       description TEXT,
                       created_at INTEGER,
                       creator_pin TEXT)''')

    # Migrasi kolom rooms (failsafe jika DB sudah ada)
    try:
        cursor.execute("ALTER TABLE rooms ADD COLUMN password TEXT")
    except sqlite3.OperationalError:
        pass

    # 4. Tabel Bots
    # Menyimpan konfigurasi bot yang dibuat via 'xtc start:bot'
    cursor.execute('''CREATE TABLE IF NOT EXISTS bots
                      (id         INTEGER PRIMARY KEY AUTOINCREMENT,
                       name       TEXT NOT NULL,
                       pin        TEXT NOT NULL,
                       room       TEXT NOT NULL,
                       host       TEXT,
                       tasks      TEXT,
                       status     TEXT DEFAULT 'active',
                       created_at INTEGER DEFAULT (strftime('%s','now')))''')

    conn.commit()
    conn.close()

# Inisialisasi otomatis saat module diimport
init_tables()