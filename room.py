from db import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash

def create_room(name, creator, password=""):
    """Membuat room baru dengan password yang di-hash."""
    conn = get_db_connection()
    # Hash password jika ada, jika tidak, simpan sebagai string kosong
    hashed_pw = generate_password_hash(password) if password else ""
    
    try:
        # Asumsi: Kamu harus menambahkan kolom 'password' di tabel 'rooms' via db.py
        conn.execute(
            "INSERT INTO rooms (name, creator, password) VALUES (?, ?, ?)", 
            (name, creator, hashed_pw)
        )
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def verify_password(name, password):
    """Memverifikasi password room."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM rooms WHERE name = ?", (name,))
        row = cursor.fetchone()
        
        if row:
            stored_pw = row['password']
            # Jika tidak ada password, anggap room public (return True)
            if not stored_pw:
                return True
            # Verifikasi hash
            return check_password_hash(stored_pw, password)
        return False
    except:
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
            conn.execute("DELETE FROM messages WHERE room = ?", (name,))
            conn.execute("DELETE FROM rooms WHERE name = ?", (name,))
            conn.commit()
            return True
    except:
        return False
    finally:
        conn.close()
    
    return False