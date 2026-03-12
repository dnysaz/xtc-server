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
    """Mengambil semua room yang tidak memiliki password (Public)."""
    try:
        # Mengambil data dari modul room
        all_rooms_data = room.get_all_rooms() 
        
        # Filter hanya yang password-nya kosong atau None
        public_rooms = [
            {"name": r['name']} 
            for r in all_rooms_data 
            if not r.get('password')
        ]
        
        return jsonify({
            "status": "success",
            "rooms": public_rooms,
            "count": len(public_rooms)
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
    data = request.get_json()
    room_name = data.get('room')
    password = data.get('password', '')
    
    if not room.room_exists(room_name):
        return jsonify({"status": "failed", "message": "room_not_found"}), 404

    if room.verify_password(room_name, password):
        success = connection.save_message(room_name, data['user'], data['content'])
        return jsonify({"status": "success" if success else "failed"}), 201
    return jsonify({"status": "failed", "message": "Invalid password"}), 403

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