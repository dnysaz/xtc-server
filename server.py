from flask import Flask, request, jsonify
import db
import room
import connection

app = Flask(__name__)

# Initialize database tables on startup
db.init_tables()

@app.route('/create-room', methods=['POST'])
def create_room_route():
    # Expecting: {"room": "name", "user": "linux_username"}
    data = request.json
    success = room.create_room(data['room'], data['user'])
    return jsonify({"status": "success" if success else "failed"}), 201

@app.route('/delete-room', methods=['POST'])
def delete_room_route():
    # Expecting: {"room": "name", "user": "linux_username"}
    data = request.json
    success = room.delete_room(data['room'], data['user'])
    return jsonify({"status": "success" if success else "failed"}), 200

@app.route('/send', methods=['POST'])
def send_message_route():
    data = request.get_json()
    if not data or 'room' not in data or 'user' not in data or 'content' not in data:
        return jsonify({"status": "failed", "message": "Missing parameters"}), 400
    
    success = connection.save_message(data['room'], data['user'], data['content'])
    return jsonify({"status": "success" if success else "failed"}), 201

@app.route('/messages/<room_name>', methods=['GET'])
def get_messages_route(room_name):
    msgs = connection.get_messages(room_name)
    return jsonify(msgs), 200

if __name__ == '__main__':
    # Running the server
    app.run(host='0.0.0.0', port=8080)