print("Starting test server...", flush=True)
from flask import Flask
from flask_socketio import SocketIO
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

@socketio.on('connect')
def handle_connect():
    print("Client connected", flush=True)

if __name__ == '__main__':
    print("Running socketio...", flush=True)
    socketio.run(app, debug=True, port=5001, allow_unsafe_werkzeug=True)
