from db import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

def get_all_rooms():
    """Mengambil semua daftar room lengkap dengan creator dan description."""
    conn = get_db_connection()
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # UPDATE: Tambahkan kolom creator dan description dalam SELECT
        cursor.execute("SELECT name, password, creator, description FROM rooms")
        rows = cursor.fetchall()
        
        rooms = []
        for row in rows:
            # Jika kolom password berisi hash, maka has_password = True
            rooms.append({
                "name": row['name'],
                "has_password": True if row['password'] and row['password'].strip() != "" else False,
                "creator": row['creator'] if row['creator'] else "SYSTEM",
                "description": row['description'] if row['description'] else "No description provided."
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

def create_room(name, creator, password="", description="", created_at=""):
    """Membuat room baru dengan deskripsi. Password opsional."""
    conn = get_db_connection()
    
    # Logic: Jika password kosong/hanya spasi, simpan "" agar statusnya OPEN
    hashed_pw = generate_password_hash(password) if (password and password.strip() != "") else ""
    
    try:
        # PENTING: Query INSERT sekarang harus mencakup 5 kolom
        conn.execute(
            "INSERT INTO rooms (name, creator, password, description) VALUES (?, ?, ?, ?, ?)", 
            (name, creator, hashed_pw, description, created_at)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Terjadi jika nama room sudah ada (UNIQUE constraint)
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
        # Gunakan Row factory untuk akses kolom dengan nama
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM rooms WHERE name = ?", (name,))
        row = cursor.fetchone()
        
        if row:
            stored_pw = row['password']
            # Jika password di DB kosong, berarti room publik (Akses diizinkan)
            if not stored_pw or stored_pw.strip() == "":
                return True
            # Jika ada hash, bandingkan dengan password input
            return check_password_hash(stored_pw, password)
        return False
    except Exception as e:
        print(f"Error verifying password: {e}")
        return False
    finally:
        conn.close()

def delete_room(name):
    """
    Menghapus room dan pesan di dalamnya secara permanen.
    Validasi creator dilakukan di level server.py untuk fleksibilitas.
    """
    conn = get_db_connection()
    try:
        with conn:
            # Hapus pesan terkait agar DB tetap bersih (Foreign Key simulation)
            conn.execute("DELETE FROM messages WHERE room = ?", (name,))
            # Hapus room
            cursor = conn.execute("DELETE FROM rooms WHERE name = ?", (name,))
            
            # Jika rowcount > 0 berarti ada yang terhapus
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Error executing delete in DB: {e}")
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
        # Room terproteksi jika kolom password tidak null dan tidak kosong
        return row is not None and row['password'] != ""
    except:
        return False
    finally:
        conn.close()