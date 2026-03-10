from db import get_db_connection

def save_message(room, sender, content):
    """Menyimpan pesan baru ke tabel messages."""
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO messages (room, sender, content) VALUES (?, ?, ?)", 
                     (room, sender, content))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def get_messages(room):
    """Mengambil semua pesan untuk room tertentu."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Mengambil pesan dan mengurutkan berdasarkan ID (urutan waktu)
    cursor.execute("SELECT sender, content FROM messages WHERE room = ? ORDER BY id ASC", (room,))
    rows = cursor.fetchall()
    conn.close()
    
    # Mengubah hasil query menjadi list of dict agar mudah dikonversi ke JSON
    return [{"sender": row['sender'], "content": row['content']} for row in rows]