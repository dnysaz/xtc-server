import sys
import os
import signal
import subprocess
from flask import Flask, request, jsonify
import db
import room
import connection
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
PID_FILE = "server.pid"

# Initialize database tables on startup
db.init_tables()

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "status": "online",
        "service": "XtermChat Gateway",
        "version": "1.0"
    }), 200

# --- ROUTE BARU: LIST PUBLIC ROOMS ---
@app.route('/rooms', methods=['GET'])
def list_rooms_route():
    """Mengambil semua room dengan status password untuk CLI dan Web."""
    try:
        # Mengambil data dari modul room (yang sudah kita update di db.py)
        # Pastikan room.get_all_rooms() memanggil fungsi di db.py yang baru
        all_rooms_data = room.get_all_rooms() 
        
        # Jangan di-filter! Kirim semua, tapi gunakan flag has_password
        rooms_to_send = []
        for r in all_rooms_data:
            rooms_to_send.append({
                "name": r['name'],
                "has_password": r.get('has_password', False)
            })
        
        return jsonify({
            "status": "success",
            "rooms": rooms_to_send,
            "count": len(rooms_to_send)
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/create-room', methods=['POST'])
def create_room_route():
    data = request.json
    room_name = data.get('room')
    user = data.get('user')
    password = data.get('password', '')
    success = room.create_room(room_name, user, password)
    return jsonify({"status": "success" if success else "failed"}), 201

@app.route('/delete-room', methods=['POST'])
def delete_room_route():
    data = request.json
    room_name = data.get('room')
    user = data.get('user')
    success = room.delete_room(room_name, user)
    return jsonify({"status": "success" if success else "failed"}), 200

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

@app.route('/send', methods=['POST'])
def send_message_route():
    data = request.json
    username = data.get('user')
    user_pin = data.get('pin') # PIN dari Web atau CLI
    
    # Cek apakah username ini terdaftar di tabel users
    conn = db.get_db_connection()
    user_record = conn.execute('SELECT pin FROM users WHERE username = ?', (username,)).fetchone()
    
    if user_record:
        # Jika terdaftar, wajib cek PIN
        if user_record['pin'] != str(user_pin):
            return jsonify({"status": "failed", "message": "Identity mismatch. Wrong PIN."}), 403

    # Jika lolos (atau user belum terdaftar), simpan pesan
    success = connection.save_message(username, data['content'], user_pin)
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
        print("[!] Server is already running or pid file exists.")
        return
    cmd = [sys.executable, "server.py", "run_internal"]
    with open("server.log", "a") as log:
        process = subprocess.Popen(cmd, stdout=log, stderr=log, preexec_fn=os.setpgrp)
        with open(PID_FILE, "w") as f:
            f.write(str(process.pid))
    print(f"[*] Server started in background (PID: {process.pid})")
    print("[*] Logs: tail -f server.log")

def stop_server():
    if not os.path.exists(PID_FILE):
        print("[!] Server is not running.")
        return
    with open(PID_FILE, "r") as f:
        pid = int(f.read())
    try:
        os.kill(pid, signal.SIGTERM)
        os.remove(PID_FILE)
        print(f"[*] Server (PID: {pid}) stopped successfully.")
    except ProcessLookupError:
        os.remove(PID_FILE)
        print("[!] PID file found but process not active. Cleaned up.")

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
        app.run(host='0.0.0.0', port=8080)