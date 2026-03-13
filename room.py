from db import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

def get_all_rooms():
    """Mengambil daftar room lengkap termasuk creator_pin untuk validasi keamanan."""
    conn = get_db_connection()
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # UPDATE: creator_pin HARUS ditarik agar server bisa melakukan validasi PIN
        cursor.execute("SELECT name, password, creator, description, created_at, creator_pin FROM rooms")
        rows = cursor.fetchall()
        
        rooms = []
        for row in rows:
            rooms.append({
                "name": row['name'],
                "has_password": True if (row['password'] and row['password'].strip() != "") else False,
                "creator": row['creator'] if row['creator'] else "SYSTEM",
                "description": row['description'] if row['description'] else "No description provided.",
                "created_at": row['created_at'] if row['created_at'] else 0,
                "creator_pin": row['creator_pin'] # Data krusial untuk fitur :purge
            })
        return rooms
    except Exception as e:
        print(f"Error fetching all rooms: {e}")
        return []
    finally:
        conn.close()

def room_exists(name):
    """Mengecek apakah room ada di database."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM rooms WHERE name = ?", (name,))
        return cursor.fetchone() is not None
    except Exception as e:
        print(f"Error checking room existence: {e}")
        return False
    finally:
        conn.close()

def create_room(name, creator, password="", description="", created_at=0, creator_pin=""):
    """Membuat room baru dengan identitas unik creator_pin (Hardware ID)."""
    conn = get_db_connection()
    hashed_pw = generate_password_hash(password) if (password and password.strip() != "") else ""
    
    try:
        conn.execute(
            "INSERT INTO rooms (name, creator, password, description, created_at, creator_pin) VALUES (?, ?, ?, ?, ?, ?)", 
            (name, creator, hashed_pw, description, created_at, creator_pin)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        print(f"Error creating room: {e}")
        return False
    finally:
        conn.close()

def verify_password(name, password):
    """Memverifikasi password room (True jika publik atau password benar)."""
    conn = get_db_connection()
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM rooms WHERE name = ?", (name,))
        row = cursor.fetchone()
        
        if row:
            stored_pw = row['password']
            if not stored_pw or stored_pw.strip() == "":
                return True
            return check_password_hash(stored_pw, password)
        return False
    except Exception as e:
        print(f"Error verifying password: {e}")
        return False
    finally:
        conn.close()

def delete_room(name):
    """Menghapus room dan pesan di dalamnya secara permanen."""
    conn = get_db_connection()
    try:
        with conn:
            conn.execute("DELETE FROM messages WHERE room = ?", (name,))
            cursor = conn.execute("DELETE FROM rooms WHERE name = ?", (name,))
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Error executing delete in DB: {e}")
        return False
    finally:
        conn.close()

def purge_messages(name):
    """Menghapus semua pesan dalam room tertentu (Server-Side)."""
    conn = get_db_connection()
    try:
        with conn:
            conn.execute("DELETE FROM messages WHERE room = ?", (name,))
        return True
    except Exception as e:
        print(f"Error purging messages: {e}")
        return False
    finally:
        conn.close()
        
def is_password_protected(name):
    """Mengecek apakah room memiliki password (bukan string kosong)."""
    conn = get_db_connection()
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM rooms WHERE name = ?", (name,))
        row = cursor.fetchone()
        return row is not None and row['password'] != ""
    except:
        return False
    finally:
        conn.close()