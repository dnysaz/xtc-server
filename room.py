from db import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

def get_all_rooms():
    """Mengambil semua daftar room dari database."""
    conn = get_db_connection()
    try:
        # Menggunakan Row factory agar bisa diakses seperti dictionary
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT name, password FROM rooms")
        return [dict(row) for row in cursor.fetchall()]
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

def create_room(name, creator, password=""):
    """Membuat room baru dengan password yang di-hash."""
    conn = get_db_connection()
    hashed_pw = generate_password_hash(password) if password else ""
    
    try:
        conn.execute(
            "INSERT INTO rooms (name, creator, password) VALUES (?, ?, ?)", 
            (name, creator, hashed_pw)
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
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM rooms WHERE name = ?", (name,))
        row = cursor.fetchone()
        
        if row:
            stored_pw = row['password']
            if not stored_pw:
                return True
            return check_password_hash(stored_pw, password)
        return False
    except Exception as e:
        print(f"Error verifying password: {e}")
        return False
    finally:
        conn.close()

def delete_room(name, requester):
    """Menghapus room hanya jika requester adalah pemiliknya."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT creator FROM rooms WHERE name = ?", (name,))
        row = cursor.fetchone()
        
        if row and row['creator'] == requester:
            with conn:
                conn.execute("DELETE FROM messages WHERE room = ?", (name,))
                conn.execute("DELETE FROM rooms WHERE name = ?", (name,))
            return True
    except Exception as e:
        print(f"Error deleting room: {e}")
        return False
    finally:
        conn.close()
    
    return False

def is_password_protected(name):
    """Mengecek apakah room memiliki password (bukan string kosong)."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM rooms WHERE name = ?", (name,))
        row = cursor.fetchone()
        return row is not None and row['password'] != ""
    except:
        return False
    finally:
        conn.close()