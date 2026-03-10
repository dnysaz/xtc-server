from db import get_db_connection

def create_room(name, creator):
    """Membuat room baru dan mencatat siapa creator-nya."""
    conn = get_db_connection()
    try:
        # Menggunakan parameter binding untuk mencegah SQL injection
        conn.execute("INSERT INTO rooms (name, creator) VALUES (?, ?)", (name, creator))
        conn.commit()
        return True
    except:
        return False  # Return False jika room sudah ada (constraint UNIQUE)
    finally:
        conn.close()

def delete_room(name, requester):
    """Menghapus room hanya jika requester adalah pemiliknya (creator)."""
    conn = get_db_connection()
    # Menggunakan with untuk memastikan koneksi ditutup otomatis
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT creator FROM rooms WHERE name = ?", (name,))
        row = cursor.fetchone()
        
        # Validasi: Room harus ada dan requester harus sama dengan creator
        if row and row['creator'] == requester:
            # Hapus pesan terlebih dahulu untuk menjaga integritas
            conn.execute("DELETE FROM messages WHERE room = ?", (name,))
            # Baru hapus room-nya
            conn.execute("DELETE FROM rooms WHERE name = ?", (name,))
            conn.commit()
            return True
    except:
        return False
    finally:
        conn.close()
    
    return False