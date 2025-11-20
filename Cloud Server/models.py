from datetime import datetime
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash


class Account(db.Model):
    __tablename__ = 'account'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to robots (through UserRobot)
    # user_robots relationship is auto-created in UserRobot model

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self, include_robots=False):
        d = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat()
        }
        if include_robots:
            d['robots'] = [ur.to_dict() for ur in self.user_robots]
        return d


class Sensor(db.Model):
    __tablename__ = 'sensor'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    sensor_type = db.Column(db.String(80), nullable=True)
    robot_id = db.Column(db.Integer, db.ForeignKey('robot.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to sensor data readings
    readings = db.relationship('SensorData', backref='sensor', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'sensor_type': self.sensor_type,
            'robot_id': self.robot_id,
            'created_at': self.created_at.isoformat()
        }


class SensorData(db.Model):
    """Stores individual sensor readings/data points"""
    __tablename__ = 'sensor_data'
    id = db.Column(db.Integer, primary_key=True)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensor.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    value = db.Column(db.Float, nullable=False)  # The actual sensor reading
    unit = db.Column(db.String(20), nullable=True)  # e.g., "°C", "hPa", "%"
    extra_data = db.Column(db.Text, nullable=True)  # Optional: store additional data as JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'sensor_id': self.sensor_id,
            'timestamp': self.timestamp.isoformat(),
            'value': self.value,
            'unit': self.unit,
            'extra_data': self.extra_data,
            'created_at': self.created_at.isoformat()
        }


class Robot(db.Model):
    """Represents a physical Viam robot (can be shared by multiple users)"""
    __tablename__ = 'robot'
    id = db.Column(db.Integer, primary_key=True)
    robot_name = db.Column(db.String(120), nullable=False)
    viam_robot_address = db.Column(db.String(256), unique=True, nullable=False)  # Unique identifier
    status = db.Column(db.String(20), default='disconnected')  # online, offline, disconnected
    last_connected = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user_robots = db.relationship('UserRobot', backref='robot', cascade='all, delete-orphan', lazy=True)
    sensors = db.relationship('Sensor', backref='robot', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'robot_name': self.robot_name,
            'viam_robot_address': self.viam_robot_address,
            'status': self.status,
            'last_connected': self.last_connected.isoformat() if self.last_connected else None,
            'created_at': self.created_at.isoformat()
        }


class UserRobot(db.Model):
    """Junction table: User's connection to a Robot (stores credentials)"""
    __tablename__ = 'user_robot'
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    robot_id = db.Column(db.Integer, db.ForeignKey('robot.id'), nullable=False)
    viam_api_key = db.Column(db.String(256), nullable=False)  # User's credentials for this robot
    viam_api_key_id = db.Column(db.String(256), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    account = db.relationship('Account', backref='user_robots')

    def to_dict(self):
        return {
            'id': self.id,
            'robot_id': self.robot_id,
            'robot_name': self.robot.robot_name,
            'viam_robot_address': self.robot.viam_robot_address,
            'status': self.robot.status,
            'last_connected': self.robot.last_connected.isoformat() if self.robot.last_connected else None,
            'added_at': self.added_at.isoformat()
        }
