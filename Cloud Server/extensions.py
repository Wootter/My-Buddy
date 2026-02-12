from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

# Create DB instance here so it can be imported without circular imports.
db = SQLAlchemy()
socketio = SocketIO()
