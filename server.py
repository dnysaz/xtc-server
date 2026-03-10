from flask import Flask, request, jsonify
import db
import room
import connection

app = Flask(__name__)

# Initialize database tables on startup
db.init_tables()

@app.route('/create-room', methods=['POST'])
def create_room_route():
    # Expecting: {"room": "name", "user": "linux_username", "password": "optional_password"}
    data = request.json
    room_name = data.get('room')
    user = data.get('user')
    password = data.get('password', '')
    
    success = room.create_room(room_name, user, password)
    return jsonify({"status": "success" if success else "failed"}), 201

@app.route('/delete-room', methods=['POST'])
def delete_room_route():
    # Expecting: {"room": "name", "user": "linux_username"}
    data = request.json
    success = room.delete_room(data['room'], data['user'])
    return jsonify({"status": "success" if success else "failed"}), 200

@app.route('/send', methods=['POST'])
def send_message_route():
    # Expecting: {"room": "name", "user": "linux_username", "content": "msg", "password": "..."}
    data = request.get_json()
    if not data or 'room' not in data or 'user' not in data or 'content' not in data:
        return jsonify({"status": "failed", "message": "Missing parameters"}), 400
    
    password = data.get('password', '')
    
    # Validasi akses room sebelum simpan pesan
    if room.verify_password(data['room'], password):
        success = connection.save_message(data['room'], data['user'], data['content'])
        return jsonify({"status": "success" if success else "failed"}), 201
    else:
        return jsonify({"status": "failed", "message": "Invalid password"}), 403

@app.route('/messages/<room_name>', methods=['GET'])
def get_messages_route(room_name):
    password = request.args.get('password', '')
    
    if room.verify_password(room_name, password):
        msgs = connection.get_messages(room_name)
        return jsonify(msgs), 200
    else:
        return jsonify({"status": "failed", "message": "Invalid password"}), 403

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)