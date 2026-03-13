import sys
import os
import signal
import subprocess
from time import time
from flask import Flask, request, jsonify
from flask_cors import CORS
import db
import room
import connection

app = Flask(__name__)

# FIX CORS: Izinkan semua metode dan header agar preflight OPTIONS tidak error
CORS(app, resources={r"/*": {
    "origins": "*",
    "methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"]
}}, supports_credentials=True)

PID_FILE = "server.pid"

# Initialize database tables on startup
db.init_tables()

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "status": "online",
        "service": "XtermChat Gateway",
        "version": "1.1"
    }), 200

# --- IDENTITY & AUTHENTICATION ---
@app.route('/login', methods=['POST', 'OPTIONS'])
def login_check():
    """Route untuk memverifikasi atau mendaftarkan identitas (Name + PIN)."""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
        
    data = request.json
    username = data.get('user', '').strip().lower()
    pin = str(data.get('pin', ''))

    if not username or not pin:
        return jsonify({"status": "failed", "message": "Missing credentials"}), 400

    conn = db.get_db_connection()
    try:
        user_record = conn.execute('SELECT pin FROM users WHERE username = ?', (username,)).fetchone()
        
        if user_record:
            if user_record['pin'] == pin:
                return jsonify({"status": "success", "message": "Welcome back"}), 200
            else:
                return jsonify({"status": "failed", "message": "Identity locked to another device/PIN."}), 403
        else:
            # Register user baru secara otomatis
            conn.execute('INSERT INTO users (username, pin) VALUES (?, ?)', (username, pin))
            conn.commit()
            return jsonify({"status": "success", "message": "New identity registered"}), 201
    finally:
        conn.close()

# --- ROOM MANAGEMENT ---
@app.route('/rooms', methods=['GET'])
def list_rooms_route():
    try:
        # room.get_all_rooms() sekarang sudah membawa data created_at
        all_rooms_data = room.get_all_rooms() 
        
        rooms_to_send = []
        for r in all_rooms_data:
            rooms_to_send.append({
                "name": r.get('name'),
                "has_password": r.get('has_password', False),
                "creator": r.get('creator', 'SYSTEM'),   
                "description": r.get('description', ''),
                "created_at": r.get('created_at', 0)  
            })
            
        return jsonify({
            "status": "success", 
            "rooms": rooms_to_send, 
            "count": len(rooms_to_send)
        }), 200
    except Exception as e:
        print(f"Error in list_rooms_route: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/create-room', methods=['POST'])
def create_room_route():
    data = request.json
    
    # Ambil data dari JSON payload
    room_name = data.get('room')
    user = data.get('user')
    password = data.get('password', '')
    description = data.get('description', '')
    created_at = data.get('created_at', 0)
    creator_pin = data.get('pin', '')

    # Kirim ke modul room (Sekarang mengirim 6 argumen termasuk creator_pin)
    success = room.create_room(
        room_name, 
        user, 
        password, 
        description, 
        created_at, 
        creator_pin
    )
    
    if success:
        return jsonify({"status": "success", "message": f"Room @{room_name} created."}), 201
    else:
        # Pesan error lebih spesifik untuk membantu debugging
        return jsonify({"status": "failed", "message": "Room already exists or invalid data schema."}), 400
@app.route('/verify-room', methods=['POST'])
def verify_room_route():
    data = request.json
    room_name = data.get('room')
    password = data.get('password', '')

    if not room.room_exists(room_name):
        return jsonify({"status": "failed", "message": "room_not_found"}), 404

    if room.is_password_protected(room_name):
        if room.verify_password(room_name, password):
            return jsonify({"status": "success"}), 200
        return jsonify({"status": "failed", "message": "wrong_password"}), 403
    
    return jsonify({"status": "success"}), 200

# --- ROOM DELETION ---
@app.route('/delete-room', methods=['POST'])
def delete_room_route():
    data = request.json
    room_name = data.get('room')
    request_user = data.get('user', '').strip().lower()

    if not room_name:
        return jsonify({"status": "error", "message": "Room name is required"}), 400

    if not room.room_exists(room_name):
        return jsonify({"status": "error", "message": "Room not found"}), 404

    # Ambil info room untuk cek siapa creator-nya
    all_rooms = room.get_all_rooms()
    target_room = next((r for r in all_rooms if r['name'] == room_name), None)

    if target_room:
        creator = target_room.get('creator', '').strip().lower()
        
        # Validasi: Hanya creator atau 'system' yang bisa hapus
        if creator != request_user and request_user != 'admin':
            return jsonify({
                "status": "failed", 
                "message": f"Unauthorized. Only '{creator}' can delete this room."
            }), 403

    # Jika valid, lakukan penghapusan
    try:
        success = room.delete_room(room_name)
        if success:
            return jsonify({"status": "success", "message": f"Room @{room_name} deleted."}), 200
        else:
            return jsonify({"status": "failed", "message": "Database error during deletion."}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- MESSAGING ---
@app.route('/send', methods=['POST', 'OPTIONS'])
def send_message_route():
    if request.method == "OPTIONS":
        return jsonify({"ok": True}), 200

    data = request.json
    username = data.get('user', '').strip().lower()
    user_pin = str(data.get('pin', ''))
    room_name = data.get('room')
    content = data.get('content')
    
    conn = db.get_db_connection()
    user_record = conn.execute('SELECT pin FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    
    if user_record:
        if user_record['pin'] != user_pin:
            return jsonify({"status": "failed", "message": "Identity mismatch. Wrong PIN."}), 403
    else:
        # Failsafe untuk CLI: Daftar otomatis jika belum ada di tabel users
        conn = db.get_db_connection()
        conn.execute('INSERT INTO users (username, pin) VALUES (?, ?)', (username, user_pin))
        conn.commit()
        conn.close()

    # Simpan pesan ke database
    success = connection.save_message(room_name, data.get('user'), content, user_pin)
    
    return jsonify({"status": "success"}), 201

@app.route('/messages/<room_name>', methods=['GET'])
def get_messages_route(room_name):
    if not room.room_exists(room_name):
        return jsonify({"status": "failed", "message": "room_not_found"}), 404

    password = request.args.get('password', '')
    if room.is_password_protected(room_name):
        if not room.verify_password(room_name, password):
            return jsonify({"status": "failed", "message": "password_required"}), 401
    
    msgs = connection.get_messages(room_name)
    return jsonify(msgs), 200

@app.route('/purge-chat', methods=['POST'])
def purge_chat_route():
    data = request.json
    room_name = data.get('room')
    
    # Tambahkan .strip().lower() untuk menghindari perbedaan format
    requester_pin = str(data.get('pin', '')).strip().lower()
    
    # 1. Cari data room di database
    all_rooms = room.get_all_rooms()
    target_room = next((r for r in all_rooms if r['name'] == room_name), None)
    
    if not target_room:
        return jsonify({"status": "error", "message": "Room not found"}), 404

    # Ambil owner_pin dan bersihkan juga formatnya
    owner_pin = str(target_room.get('creator_pin', '')).strip().lower()

    # Validasi jika PIN di database kosong (NULL)
    if not owner_pin or owner_pin == "none" or owner_pin == "":
        return jsonify({"status": "error", "message": "Room owner identity not set. Cannot purge."}), 403
    
    # Bandingkan PIN yang sudah dibersihkan
    if owner_pin != requester_pin:
        print(f"[SECURITY] Unauthorized purge attempt on @{room_name} by PIN {requester_pin}")
        return jsonify({"status": "error", "message": "Unauthorized: Hardware ID mismatch."}), 403

    # Eksekusi penghapusan
    if room.purge_messages(room_name):
        print(f"[SUCCESS] Room @{room_name} database has been purged by Owner.")
        return jsonify({"status": "success", "message": "History cleared successfully."}), 200
    
    return jsonify({"status": "error", "message": "Database error during purge."}), 500

# --- BACKGROUND PROCESS LOGIC ---
def start_server():
    if os.path.exists(PID_FILE):
        print("[!] Server is already running.")
        return
    cmd = [sys.executable, "server.py", "run_internal"]
    with open("server.log", "a") as log:
        process = subprocess.Popen(cmd, stdout=log, stderr=log, preexec_fn=os.setpgrp)
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
        print(f"[*] Server stopped.")
    except:
        os.remove(PID_FILE)
        print("[!] Cleaned up PID file.")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "start": start_server()
        elif command == "stop": stop_server()
        elif command == "run_internal":
            app.run(host='0.0.0.0', port=8080, debug=False)
    else:
        app.run(host='0.0.0.0', port=8080)