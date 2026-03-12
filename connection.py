from db import get_db_connection
from datetime import datetime

def save_message(room, sender, content, pin=None):
    """Menyimpan pesan baru ke tabel messages dengan verifikasi PIN identity."""
    conn = get_db_connection()
    try:
        # Gunakan format waktu lokal server agar sinkron dengan db.py
        # SQLite datetime('now', 'localtime') akan menangani default jika timestamp None
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn.execute(
            "INSERT INTO messages (room, sender, content, pin, timestamp) VALUES (?, ?, ?, ?, ?)", 
            (room, sender, content, pin, timestamp)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving message: {e}")
        return False
    finally:
        conn.close()

def get_messages(room):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT sender, content, pin, timestamp FROM messages WHERE room = ? ORDER BY id ASC", 
            (room,)
        )
        rows = cursor.fetchall()
        
        return [
            {
                "sender": row['sender'], 
                "content": row['content'], 
                "pin": row['pin'],
                "timestamp": row['timestamp']
            } for row in rows
        ]
    finally:
        conn.close()