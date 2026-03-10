from db import get_db_connection

def register_user(username):
    """Mencatat user ke sistem (opsional, untuk metadata tambahan)."""
    conn = get_db_connection()
    try:
        conn.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (username,))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def is_admin(username):
    """Cek apakah user memiliki hak akses admin global."""
    # Contoh implementasi sederhana
    return username in ["admin", "root","user"]