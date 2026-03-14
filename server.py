import sys
import os
import signal
import subprocess
from flask import Flask, request, jsonify
from flask_cors import CORS
import db
import room
import connection

app = Flask(__name__)

# CORS: Allow all origins, methods, headers
CORS(app, resources={r"/*": {
    "origins": "*",
    "methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"]
}}, supports_credentials=True)

PID_FILE = "server.pid"

# Initialize database tables on startup
db.init_tables()


# ─── HEALTH CHECK ─────────────────────────────────────────────────────────────

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "status": "online",
        "service": "XtermChat Gateway",
        "version": "1.1"
    }), 200


# ─── IDENTITY & AUTHENTICATION ────────────────────────────────────────────────

@app.route('/login', methods=['POST', 'OPTIONS'])
def login_check():
    """Verifikasi atau daftarkan identitas user (username + PIN)."""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.json
    if not data:
        return jsonify({"status": "failed", "message": "No data provided"}), 400

    username = data.get('user', '').strip().lower()
    pin      = str(data.get('pin', '')).strip()

    if not username or not pin:
        return jsonify({"status": "failed", "message": "Missing credentials"}), 400

    conn = db.get_db_connection()
    try:
        user_record = conn.execute(
            'SELECT pin FROM users WHERE username = ?', (username,)
        ).fetchone()

        if user_record:
            if user_record['pin'] == pin:
                return jsonify({"status": "success", "message": "Welcome back"}), 200
            else:
                return jsonify({
                    "status": "failed",
                    "message": "Identity locked to another device/PIN."
                }), 403
        else:
            conn.execute(
                'INSERT INTO users (username, pin) VALUES (?, ?)', (username, pin)
            )
            conn.commit()
            return jsonify({"status": "success", "message": "New identity registered"}), 201
    finally:
        conn.close()


# ─── ROOM MANAGEMENT ──────────────────────────────────────────────────────────

@app.route('/rooms', methods=['GET'])
def list_rooms_route():
    """Kembalikan semua room tanpa data sensitif (tanpa creator_pin, password)."""
    try:
        all_rooms_data = room.get_all_rooms()
        rooms_to_send  = []

        for r in all_rooms_data:
            rooms_to_send.append({
                "name":         r.get('name'),
                "has_password": r.get('has_password', False),
                "creator":      r.get('creator', 'SYSTEM'),
                "description":  r.get('description', ''),
                "created_at":   r.get('created_at', 0)
                # creator_pin TIDAK dikirim ke client — server-side only
            })

        return jsonify({
            "status": "success",
            "rooms":  rooms_to_send,
            "count":  len(rooms_to_send)
        }), 200

    except Exception as e:
        print(f"[ERROR] list_rooms_route: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/create-room', methods=['POST'])
def create_room_route():
    """Buat room baru. creator_pin wajib ada untuk proteksi delete & purge."""
    data = request.json
    if not data:
        return jsonify({"status": "failed", "message": "No data provided"}), 400

    room_name   = data.get('room', '').strip()
    user        = data.get('user', '').strip()
    password    = data.get('password', '')
    description = data.get('description', '')
    created_at  = data.get('created_at', 0)
    creator_pin = str(data.get('pin', '')).strip()

    if not room_name or not user:
        return jsonify({"status": "failed", "message": "Room name and user are required"}), 400

    if not creator_pin:
        return jsonify({"status": "failed", "message": "Hardware PIN is required to create a room"}), 400

    success = room.create_room(room_name, user, password, description, created_at, creator_pin)

    if success:
        return jsonify({"status": "success", "message": f"Room @{room_name} created."}), 201
    else:
        return jsonify({"status": "failed", "message": "Room already exists or invalid data."}), 400


@app.route('/verify-room', methods=['POST'])
def verify_room_route():
    """Cek apakah room ada dan password benar."""
    data      = request.json
    room_name = data.get('room', '').strip()
    password  = data.get('password', '')

    if not room.room_exists(room_name):
        return jsonify({"status": "failed", "message": "room_not_found"}), 404

    if room.is_password_protected(room_name):
        if room.verify_password(room_name, password):
            return jsonify({"status": "success"}), 200
        return jsonify({"status": "failed", "message": "wrong_password"}), 403

    return jsonify({"status": "success"}), 200


# ─── ROOM DELETION ─────────────────────────────────────────────────────────────

@app.route('/delete-room', methods=['POST'])
def delete_room_route():
    """
    Hapus room secara permanen beserta semua pesannya.
    Validasi: username DAN hardware PIN harus cocok dengan creator.
    Konsisten dengan mekanisme /purge-chat.
    """
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400

    room_name     = data.get('room', '').strip()
    request_user  = data.get('user', '').strip().lower()
    requester_pin = str(data.get('pin', '')).strip().lower()

    # Validasi input dasar
    if not room_name:
        return jsonify({"status": "error", "message": "Room name is required"}), 400

    if not request_user or not requester_pin:
        return jsonify({"status": "error", "message": "User and PIN are required"}), 400

    if not room.room_exists(room_name):
        return jsonify({"status": "error", "message": "Room not found"}), 404

    # Ambil data room termasuk creator_pin
    all_rooms   = room.get_all_rooms()
    target_room = next((r for r in all_rooms if r['name'] == room_name), None)

    if not target_room:
        return jsonify({"status": "error", "message": "Room not found"}), 404

    creator     = target_room.get('creator', '').strip().lower()
    creator_pin = str(target_room.get('creator_pin', '')).strip().lower()

    # Validasi creator_pin tersedia di database
    if not creator_pin or creator_pin in ('none', ''):
        return jsonify({
            "status": "error",
            "message": "Room owner identity not set. Cannot delete."
        }), 403

    # Validasi: username DAN PIN harus cocok
    if creator != request_user or creator_pin != requester_pin:
        print(f"[SECURITY] Unauthorized delete attempt on @{room_name} "
              f"by user='{request_user}' pin='{requester_pin[:8]}...'")
        return jsonify({
            "status": "failed",
            "message": "Unauthorized: Hardware ID mismatch."
        }), 403

    # Eksekusi penghapusan
    try:
        success = room.delete_room(room_name)
        if success:
            print(f"[SUCCESS] Room @{room_name} deleted by owner '{request_user}'.")
            return jsonify({
                "status": "success",
                "message": f"Room @{room_name} deleted."
            }), 200
        else:
            return jsonify({"status": "failed", "message": "Database error during deletion."}), 500
    except Exception as e:
        print(f"[ERROR] delete_room_route: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ─── MESSAGING ─────────────────────────────────────────────────────────────────

@app.route('/send', methods=['POST', 'OPTIONS'])
def send_message_route():
    """Kirim pesan ke room. Validasi identity via PIN sebelum simpan."""
    if request.method == "OPTIONS":
        return jsonify({"ok": True}), 200

    data = request.json
    if not data:
        return jsonify({"status": "failed", "message": "No data provided"}), 400

    username  = data.get('user', '').strip().lower()
    user_pin  = str(data.get('pin', '')).strip()
    room_name = data.get('room', '').strip()
    content   = data.get('content', '').strip()

    # Validasi input dasar
    if not username or not room_name:
        return jsonify({"status": "failed", "message": "Missing user or room"}), 400

    if not content:
        return jsonify({"status": "failed", "message": "Message content cannot be empty"}), 400

    # Batasi panjang pesan
    if len(content) > 4000:
        return jsonify({"status": "failed", "message": "Message too long (max 4000 chars)"}), 400

    conn        = db.get_db_connection()
    user_record = conn.execute(
        'SELECT pin FROM users WHERE username = ?', (username,)
    ).fetchone()
    conn.close()

    if user_record:
        # Validasi PIN jika user sudah terdaftar
        if user_record['pin'] != user_pin:
            return jsonify({"status": "failed", "message": "Identity mismatch. Wrong PIN."}), 403
    else:
        # Auto-register user baru (failsafe untuk CLI)
        conn = db.get_db_connection()
        conn.execute(
            'INSERT INTO users (username, pin) VALUES (?, ?)', (username, user_pin)
        )
        conn.commit()
        conn.close()

    # Simpan pesan
    connection.save_message(room_name, data.get('user'), content, user_pin)
    return jsonify({"status": "success"}), 201


@app.route('/messages/<room_name>', methods=['GET'])
def get_messages_route(room_name):
    """Ambil semua pesan di room. Validasi password jika room private."""
    if not room.room_exists(room_name):
        return jsonify({"status": "failed", "message": "room_not_found"}), 404

    password = request.args.get('password', '')
    if room.is_password_protected(room_name):
        if not room.verify_password(room_name, password):
            return jsonify({"status": "failed", "message": "password_required"}), 401

    msgs = connection.get_messages(room_name)
    return jsonify(msgs), 200


# ─── PURGE CHAT ────────────────────────────────────────────────────────────────

@app.route('/purge-chat', methods=['POST'])
def purge_chat_route():
    """
    Hapus semua pesan di room. Room tetap ada.
    Validasi: hardware PIN harus cocok dengan creator_pin.
    """
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400

    room_name     = data.get('room', '').strip()
    requester_pin = str(data.get('pin', '')).strip().lower()

    if not room_name or not requester_pin:
        return jsonify({"status": "error", "message": "Room and PIN are required"}), 400

    all_rooms   = room.get_all_rooms()
    target_room = next((r for r in all_rooms if r['name'] == room_name), None)

    if not target_room:
        return jsonify({"status": "error", "message": "Room not found"}), 404

    owner_pin = str(target_room.get('creator_pin', '')).strip().lower()

    if not owner_pin or owner_pin in ('none', ''):
        return jsonify({
            "status": "error",
            "message": "Room owner identity not set. Cannot purge."
        }), 403

    if owner_pin != requester_pin:
        print(f"[SECURITY] Unauthorized purge attempt on @{room_name} "
              f"by PIN '{requester_pin[:8]}...'")
        return jsonify({
            "status": "error",
            "message": "Unauthorized: Hardware ID mismatch."
        }), 403

    if room.purge_messages(room_name):
        print(f"[SUCCESS] Room @{room_name} purged by owner.")
        return jsonify({"status": "success", "message": "History cleared successfully."}), 200

    return jsonify({"status": "error", "message": "Database error during purge."}), 500


# ─── BACKGROUND PROCESS ────────────────────────────────────────────────────────

def start_server():
    if os.path.exists(PID_FILE):
        print("[!] Server is already running.")
        return
    cmd = [sys.executable, "server.py", "run_internal"]
    with open("server.log", "a") as log:
        process = subprocess.Popen(
            cmd, stdout=log, stderr=log, preexec_fn=os.setpgrp
        )
        with open(PID_FILE, "w") as f:
            f.write(str(process.pid))
    print(f"[*] Server started in background (PID: {process.pid})")


def stop_server():
    if not os.path.exists(PID_FILE):
        print("[!] Server is not running.")
        return
    with open(PID_FILE, "r") as f:
        pid = int(f.read())
    try:
        os.kill(pid, signal.SIGTERM)
        os.remove(PID_FILE)
        print("[*] Server stopped.")
    except:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        print("[!] Cleaned up PID file.")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "start":
            start_server()
        elif command == "stop":
            stop_server()
        elif command == "run_internal":
            app.run(host='0.0.0.0', port=8080, debug=False)
        else:
            print(f"[!] Unknown command: {command}")
            print("    Usage: python3 server.py [start|stop]")
    else:
        app.run(host='0.0.0.0', port=8080)