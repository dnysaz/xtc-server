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
        all_rooms_data = room.get_all_rooms() 
        rooms_to_send = []
        for r in all_rooms_data:
            rooms_to_send.append({
                "name": r['name'],
                "has_password": r.get('has_password', False)
            })
        return jsonify({"status": "success", "rooms": rooms_to_send, "count": len(rooms_to_send)}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/create-room', methods=['POST'])
def create_room_route():
    data = request.json
    success = room.create_room(data.get('room'), data.get('user'), data.get('password', ''))
    return jsonify({"status": "success" if success else "failed"}), 201

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