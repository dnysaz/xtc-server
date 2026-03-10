from db import get_db_connection
from datetime import datetime, timezone

def save_message(room, sender, content):
    """Menyimpan pesan baru ke tabel messages beserta timestamp."""
    conn = get_db_connection()
    try:
        # Menambahkan timestamp saat pesan disimpan
        timestamp = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO messages (room, sender, content, timestamp) VALUES (?, ?, ?, ?)", 
            (room, sender, content, timestamp)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving message: {e}")
        return False
    finally:
        conn.close()

def get_messages(room):
    """Mengambil semua pesan untuk room tertentu termasuk timestamp-nya."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Mengambil sender, content, dan timestamp
        cursor.execute(
            "SELECT sender, content, timestamp FROM messages WHERE room = ? ORDER BY id ASC", 
            (room,)
        )
        rows = cursor.fetchall()
        
        # Mengembalikan list of dict agar kompatibel dengan JSON response
        return [{"sender": row['sender'], "content": row['content'], "timestamp": row['timestamp']} for row in rows]
    finally:
        conn.close()