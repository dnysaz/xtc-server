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
    """Mengambil riwayat pesan termasuk data PIN untuk verifikasi bubble di Web."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Kita ambil kolom 'pin' juga agar Frontend bisa melakukan perbandingan isMe
        cursor.execute(
            "SELECT sender, content, pin, timestamp FROM messages WHERE room = ? ORDER BY id ASC", 
            (room,)
        )
        rows = cursor.fetchall()
        
        # Mapping data ke format JSON yang siap dikonsumsi Web dan CLI
        return [
            {
                "sender": row['sender'], 
                "content": row['content'], 
                "pin": row['pin'],
                "created_at": row['timestamp'] # Gunakan key created_at agar match dengan script chat.html
            } for row in rows
        ]
    except Exception as e:
        print(f"Error fetching messages: {e}")
        return []
    finally:
        conn.close()