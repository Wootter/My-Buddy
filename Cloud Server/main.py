# -*- coding: utf-8 -*-

'''
Filename: main.py
Author: Wout Deelen
Date: 20-10-2025
Version: 1.1
Description: Flask app with SQLAlchemy models and example API endpoints.
'''

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from functools import wraps
from config import Config
from extensions import db
from flask_migrate import Migrate
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__,
            static_url_path='/static',
            static_folder='static',
            template_folder='templates')
app.config.from_object(Config)

# Initialize DB and migrations
db.init_app(app)
migrate = Migrate()
migrate.init_app(app, db)

with app.app_context():
    # Import models to register them with SQLAlchemy
    import models  # noqa: F401


# ==================== VIAM BACKGROUND SCHEDULER ====================
def scheduled_viam_fetch():
    """Fetch Viam sensor data (runs every hour)"""
    with app.app_context():
        from viam_integration import fetch_and_store_sensor_data
        logger.info("🤖 Scheduled Viam sensor data fetch started")
        fetch_and_store_sensor_data()


# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Schedule Viam data fetch every hour
scheduler.add_job(
    func=scheduled_viam_fetch,
    trigger=IntervalTrigger(hours=1),
    id='viam_sensor_fetch',
    name='Fetch Viam sensor data',
    replace_existing=True
)

# Fetch data immediately on startup (optional - comment out if you don't want this)
scheduler.add_job(
    func=scheduled_viam_fetch,
    id='viam_startup_fetch',
    name='Initial Viam sensor data fetch',
    replace_existing=True
)

# Shutdown scheduler when app exits
atexit.register(lambda: scheduler.shutdown())

logger.info("✓ Viam scheduler initialized - fetching sensor data every hour")


# ==================== ROUTES ====================


# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember')
        
        if not email or not password:
            return render_template('login.html', error='Email and password required')
        
        from models import Account
        account = Account.query.filter_by(email=email).first()
        
        if account and account.check_password(password):
            # Login successful - create session
            session['user_id'] = account.id
            session['username'] = account.username
            session['email'] = account.email
            
            # Handle "remember me" - extend session timeout to 30 days
            if remember:
                session.permanent = True
                app.permanent_session_lifetime = timedelta(days=30)
            
            flash('Login successful!', 'success')
            return redirect(url_for('profile'))
        else:
            return render_template('login.html', error='Invalid email or password')
    
    return render_template('login.html')


@app.route('/profile')
@login_required
def profile():
    from models import Account, Sensor, UserRobot
    account = Account.query.get(session['user_id'])
    
    if not account:
        session.clear()
        return redirect(url_for('login'))
    
    # Get user's robots to count sensors
    user_robots = UserRobot.query.filter_by(account_id=account.id).all()
    robot_ids = [ur.robot_id for ur in user_robots]
    
    # Count sensors for user's robots
    sensor_count = Sensor.query.filter(Sensor.robot_id.in_(robot_ids)).count() if robot_ids else 0
    
    # Prepare user data for template
    user_data = {
        'full_name': account.username,
        'role': 'Member',
        'join_date': account.created_at.strftime('%B %Y'),
        'email': account.email,
        'username': account.username,
        'status': 'Active',
        'member_since': account.created_at.strftime('%B %d, %Y'),
        'stats': {
            'data_points': sensor_count,
            'bot_interactions': 0,
            'active_hours': '0h',
            'system_uptime': '99.9%'
        },
        'devices': [],
        'recent_activity': [],
        'security': {
            'password_last_changed': 'Never',
            'two_factor_status': 'Disabled',
            'two_factor_button': 'Enable',
            'active_sessions': '1 active session'
        },
        'preferences': {
            'theme': 'Dark Mode',
            'notifications': True,
            'notifications_description': 'Receive system alerts',
            'auto_update': True
        }
    }
    
    return render_template('profile.html', user=user_data)


@app.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile (username and password)"""
    from models import Account
    
    account = Account.query.get(session['user_id'])
    
    if request.method == 'POST':
        new_username = request.form.get('username')
        new_password = request.form.get('password')
        current_password = request.form.get('current_password')
        
        # Validate current password
        if not current_password or not account.check_password(current_password):
            return jsonify({'success': False, 'error': 'Current password is incorrect'}), 400
        
        # Update username if provided and different
        if new_username and new_username != account.username:
            # Check if username already exists
            existing = Account.query.filter_by(username=new_username).first()
            if existing:
                return jsonify({'success': False, 'error': 'Username already taken'}), 400
            account.username = new_username
        
        # Update password if provided
        if new_password and len(new_password) >= 6:
            account.set_password(new_password)
        elif new_password and len(new_password) < 6:
            return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
        
        try:
            db.session.commit()
            session['username'] = account.username  # Update session with new username
            return jsonify({'success': True, 'message': 'Profile updated successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': f'Update failed: {str(e)}'}), 500
    
    return jsonify({'error': 'Method not allowed'}), 405


@app.route('/data')
@login_required
def data():
    """Display sensor data with graphs"""
    from models import Sensor, SensorData, UserRobot
    
    # Get all robots connected by current user
    account_id = session['user_id']
    user_robots = UserRobot.query.filter_by(account_id=account_id).all()
    robot_ids = [ur.robot_id for ur in user_robots]
    
    if not robot_ids:
        # User has no robots connected
        return render_template('data.html', sensor_charts=[])
    
    # Get all sensors for user's robots
    sensors = Sensor.query.filter(Sensor.robot_id.in_(robot_ids)).all()
    
    # Find the earliest timestamp from Viam sensors to align all graphs
    earliest_viam_reading = SensorData.query.join(Sensor)\
        .filter(Sensor.robot_id.in_(robot_ids))\
        .filter(Sensor.name.in_(['VEML7700 Light', 'MH-SR602 Motion', 'DHT22 Temperature', 'DHT22 Humidity']))\
        .order_by(SensorData.timestamp.asc())\
        .first()
    
    # Use the earliest Viam timestamp, or last 24 hours if no Viam data
    start_time = earliest_viam_reading.timestamp if earliest_viam_reading else datetime.utcnow() - timedelta(hours=24)
    
    # Get sensor data for charts (from start_time onwards)
    sensor_charts = []
    for sensor in sensors:
        readings = SensorData.query.filter_by(sensor_id=sensor.id)\
            .filter(SensorData.timestamp >= start_time)\
            .order_by(SensorData.timestamp.asc())\
            .limit(500)\
            .all()
        
        if readings:
            sensor_charts.append({
                'name': sensor.name,
                'type': sensor.sensor_type,
                'data': [r.to_dict() for r in readings],
                'count': len(readings)
            })
    
    return render_template('data.html', sensors=sensors, charts=sensor_charts)


@app.route('/configure')
def configure():
    return render_template('configure.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            return render_template('register.html', error='Email and password required')
        
        from models import Account
        
        # Check if account already exists
        if Account.query.filter_by(email=email).first():
            return render_template('register.html', error='Email already registered')
        
        # Create username from email (before @ sign)
        username = email.split('@')[0]
        
        # Check if username exists, if so append a number
        base_username = username
        counter = 1
        while Account.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Create new account
        account = Account(username=username, email=email)
        account.set_password(password)
        db.session.add(account)
        db.session.commit()
        
        # Auto-login after registration
        session['user_id'] = account.id
        session['username'] = account.username
        session['email'] = account.email
        flash('Registration successful!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('register.html')


@app.route('/forgot-password')
def forgot_password():
    return render_template('forgot-password.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/init-db', methods=['POST'])
def init_db():
    # Developer convenience: create tables without migrations
    db.create_all()
    return jsonify({'status': 'ok', 'msg': 'database tables created'}), 201


@app.route('/api/accounts', methods=['POST'])
def create_account():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    if not username or not password:
        return jsonify({'error': 'username and password required'}), 400

    from models import Account
    if Account.query.filter_by(username=username).first():
        return jsonify({'error': 'username already exists'}), 409

    account = Account(username=username, email=email)
    account.set_password(password)
    db.session.add(account)
    db.session.commit()
    return jsonify(account.to_dict()), 201


@app.route('/api/accounts/<int:account_id>', methods=['GET'])
def get_account(account_id):
    from models import Account
    acct = Account.query.get_or_404(account_id)
    return jsonify(acct.to_dict(include_sensors=True))


@app.route('/api/accounts/<int:account_id>/sensors', methods=['POST'])
def add_sensor(account_id):
    data = request.get_json() or {}
    name = data.get('name')
    sensor_type = data.get('sensor_type')
    if not name:
        return jsonify({'error': 'sensor name required'}), 400

    from models import Sensor, Robot
    robot = Robot.query.get_or_404(account_id)
    sensor = Sensor(name=name, sensor_type=sensor_type, robot_id=robot.id)
    db.session.add(sensor)
    db.session.commit()
    return jsonify(sensor.to_dict()), 201


@app.route('/api/robots/<int:robot_id>/sensors', methods=['GET'])
def list_sensors(robot_id):
    from models import Sensor, Robot
    robot = Robot.query.get_or_404(robot_id)
    sensors = Sensor.query.filter_by(robot_id=robot.id).all()
    return jsonify([s.to_dict() for s in sensors])


@app.route('/api/sensor-data/upload', methods=['POST'])
def upload_sensor_data():
    """
    Receives sensor data from Viam export script.
    Expects JSON: {
        "sensor_id": 1,
        "data": [
            {"timestamp": "2025-11-11T10:00:00", "value": 23.5, "unit": "°C"},
            {"timestamp": "2025-11-11T10:01:00", "value": 23.6, "unit": "°C"}
        ]
    }
    OR CSV file upload
    """
    from models import Sensor, SensorData
    
    # Check if JSON data
    if request.is_json:
        data = request.get_json()
        sensor_id = data.get('sensor_id')
        readings = data.get('data', [])
        
        if not sensor_id:
            return jsonify({'error': 'sensor_id required'}), 400
        
        # Verify sensor exists
        sensor = Sensor.query.get_or_404(sensor_id)
        
        # Insert all readings
        inserted_count = 0
        for reading in readings:
            sensor_data = SensorData(
                sensor_id=sensor_id,
                timestamp=datetime.fromisoformat(reading.get('timestamp', datetime.utcnow().isoformat())),
                value=float(reading.get('value')),
                unit=reading.get('unit'),
                extra_data=reading.get('extra_data')
            )
            db.session.add(sensor_data)
            inserted_count += 1
        
        db.session.commit()
        return jsonify({
            'status': 'ok',
            'message': f'Inserted {inserted_count} readings for sensor {sensor_id}'
        }), 201
    
    # Check if CSV file upload
    elif 'file' in request.files:
        import csv
        from io import StringIO
        
        file = request.files['file']
        sensor_id = request.form.get('sensor_id')
        
        if not sensor_id:
            return jsonify({'error': 'sensor_id required in form data'}), 400
        
        sensor = Sensor.query.get_or_404(int(sensor_id))
        
        # Read CSV
        stream = StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        inserted_count = 0
        for row in csv_reader:
            sensor_data = SensorData(
                sensor_id=sensor_id,
                timestamp=datetime.fromisoformat(row.get('timestamp', datetime.utcnow().isoformat())),
                value=float(row.get('value')),
                unit=row.get('unit', ''),
                extra_data=row.get('extra_data')
            )
            db.session.add(sensor_data)
            inserted_count += 1
        
        db.session.commit()
        return jsonify({
            'status': 'ok',
            'message': f'Inserted {inserted_count} readings from CSV'
        }), 201
    
    return jsonify({'error': 'No JSON data or file provided'}), 400


@app.route('/api/sensor-data/<int:sensor_id>', methods=['GET'])
def get_sensor_data(sensor_id):
    """Get sensor data readings with optional filtering"""
    from models import Sensor, SensorData
    
    sensor = Sensor.query.get_or_404(sensor_id)
    
    # Optional query parameters
    limit = request.args.get('limit', 1000, type=int)
    hours = request.args.get('hours', type=int)  # Last N hours
    
    query = SensorData.query.filter_by(sensor_id=sensor_id).order_by(SensorData.timestamp.desc())
    
    if hours:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        query = query.filter(SensorData.timestamp >= cutoff_time)
    
    readings = query.limit(limit).all()
    
    return jsonify({
        'sensor': sensor.to_dict(),
        'count': len(readings),
        'data': [r.to_dict() for r in reversed(readings)]  # Chronological order
    })


@app.route('/api/viam/fetch-now', methods=['POST'])
@login_required
def manual_viam_fetch():
    """Manually trigger Viam data fetch"""
    from viam_integration import fetch_and_store_sensor_data
    
    logger.info("Manual Viam fetch triggered")
    
    with app.app_context():
        result = fetch_and_store_sensor_data()
    
    if result:
        # fetch_and_store_sensor_data returns True on success
        # Get the count of readings from the last fetch
        from models import SensorData
        recent_readings = SensorData.query.filter(
            SensorData.timestamp >= datetime.utcnow() - timedelta(seconds=30)
        ).count()
        
        return jsonify({
            'success': True, 
            'status': 'ok', 
            'message': 'Sensor data fetched successfully',
            'readings_saved': recent_readings
        }), 200
    else:
        return jsonify({
            'success': False,
            'status': 'error', 
            'message': 'Failed to fetch sensor data',
            'readings_saved': 0
        }), 500


@app.route('/api/viam/test', methods=['GET'])
@login_required
def test_viam():
    """Test Viam connection using user's first robot"""
    from models import UserRobot
    from viam_integration import test_viam_connection
    
    # Get user's first robot for testing
    account_id = session['user_id']
    user_robot = UserRobot.query.filter_by(account_id=account_id).first()
    
    if not user_robot:
        return jsonify({
            'status': 'error',
            'output': 'No robots connected. Please add a robot first.'
        })
    
    # Capture output
    import io
    import sys
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    
    success = test_viam_connection(
        user_robot.viam_api_key,
        user_robot.viam_api_key_id,
        user_robot.robot.viam_robot_address
    )
    
    output = buffer.getvalue()
    sys.stdout = old_stdout
    
    return jsonify({
        'status': 'ok' if success else 'error',
        'output': output
    })


# ==================== VIAM DEVICE MANAGEMENT ====================

@app.route('/api/devices', methods=['GET'])
@login_required
def get_devices():
    """Get all robots connected by current user"""
    from models import UserRobot
    
    account_id = session['user_id']
    user_robots = UserRobot.query.filter_by(account_id=account_id).all()
    
    return jsonify({
        'success': True,
        'devices': [ur.to_dict() for ur in user_robots]
    })


@app.route('/api/devices', methods=['POST'])
@login_required
def add_device():
    """Add a robot connection for current user"""
    from models import Robot, UserRobot
    
    account_id = session['user_id']
    data = request.get_json()
    
    # Validate required fields
    required = ['robot_name', 'viam_api_key', 'viam_api_key_id', 'viam_robot_address']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    # Check if this user already has this robot
    existing_robot = Robot.query.filter_by(viam_robot_address=data['viam_robot_address']).first()
    
    if existing_robot:
        # Robot exists, check if user already has it
        existing_user_robot = UserRobot.query.filter_by(
            account_id=account_id,
            robot_id=existing_robot.id
        ).first()
        
        if existing_user_robot:
            return jsonify({'success': False, 'error': 'You already have this robot connected'}), 400
        
        robot = existing_robot
    else:
        # Create new robot
        robot = Robot(
            robot_name=data['robot_name'],
            viam_robot_address=data['viam_robot_address'],
            status='disconnected'
        )
        db.session.add(robot)
        db.session.flush()  # Get the robot ID
    
    # Create user-robot connection
    user_robot = UserRobot(
        account_id=account_id,
        robot_id=robot.id,
        viam_api_key=data['viam_api_key'],
        viam_api_key_id=data['viam_api_key_id']
    )
    
    try:
        db.session.add(user_robot)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Robot connected successfully',
            'device': user_robot.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/devices/<int:user_robot_id>', methods=['DELETE'])
@login_required
def delete_device(user_robot_id):
    """Delete a robot connection (doesn't delete robot data)"""
    from models import UserRobot
    
    account_id = session['user_id']
    user_robot = UserRobot.query.filter_by(id=user_robot_id, account_id=account_id).first()
    
    if not user_robot:
        return jsonify({'success': False, 'error': 'Device not found'}), 404
    
    try:
        db.session.delete(user_robot)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Robot disconnected successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/devices/<int:user_robot_id>/connect', methods=['POST'])
@login_required
def connect_device(user_robot_id):
    """Test connection to a robot and update status"""
    from models import UserRobot
    from viam.rpc.dial import Credentials, DialOptions
    from viam.robot.client import RobotClient
    
    account_id = session['user_id']
    user_robot = UserRobot.query.filter_by(id=user_robot_id, account_id=account_id).first()
    
    if not user_robot:
        return jsonify({'success': False, 'error': 'Device not found'}), 404
    
    try:
        # Test connection with stored credentials
        opts = RobotClient.Options.with_api_key(
            api_key=user_robot.viam_api_key,
            api_key_id=user_robot.viam_api_key_id
        )
        
        robot = RobotClient.at_address(user_robot.robot.viam_robot_address, opts)
        robot.close()
        
        # Update robot status
        user_robot.robot.status = 'online'
        user_robot.robot.last_connected = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Connected successfully',
            'device': user_robot.to_dict()
        })
    except Exception as e:
        user_robot.robot.status = 'offline'
        db.session.commit()
        return jsonify({
            'success': False,
            'error': f'Connection failed: {str(e)}',
            'device': user_robot.to_dict()
        }), 500


# ==================== SENSOR CONFIGURATION ROUTES ====================

@app.route('/api/robot/<int:robot_id>/sensors', methods=['GET'])
@login_required
def get_robot_sensors(robot_id):
    """Get all sensors for a robot"""
    from models import UserRobot, Robot, Sensor
    
    account_id = session['user_id']
    
    # Check if user has access to this robot
    user_robot = UserRobot.query.filter_by(account_id=account_id, robot_id=robot_id).first()
    if not user_robot:
        return jsonify({'success': False, 'error': 'Robot not found or access denied'}), 403
    
    robot = Robot.query.get(robot_id)
    sensors = Sensor.query.filter_by(robot_id=robot_id).all()
    
    sensor_list = [s.to_dict() for s in sensors]
    
    return jsonify({
        'success': True,
        'robot_id': robot_id,
        'robot_name': robot.robot_name,
        'sensors': sensor_list
    })


@app.route('/api/sensor/<int:sensor_id>/pins', methods=['POST'])
@login_required
def update_sensor_pins(sensor_id):
    """Update sensor pins directly in Viam's robot configuration"""
    from models import Sensor, UserRobot
    from viam.robot.client import RobotClient
    import json
    
    account_id = session['user_id']
    sensor = Sensor.query.get_or_404(sensor_id)
    
    # Verify user has access to this sensor's robot
    user_robot = UserRobot.query.filter_by(account_id=account_id, robot_id=sensor.robot_id).first()
    if not user_robot:
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        data = request.get_json() or {}
        
        # Connect to Viam robot
        opts = RobotClient.Options.with_api_key(
            api_key=user_robot.get_viam_api_key(),
            api_key_id=user_robot.get_viam_api_key_id()
        )
        robot = RobotClient.at_address(user_robot.robot.viam_robot_address, opts)
        
        # Get current robot config
        config = robot.get_config()
        
        # Find and update the component's attributes with new pins
        for component in config.components:
            if component.name == sensor.name:
                # Update component attributes with new pin information
                if 'attributes' not in component.attributes:
                    component.attributes = {}
                
                # Update pin fields in attributes
                if 'gpio_pin' in data and data['gpio_pin'] is not None:
                    component.attributes['gpio_pin'] = str(data['gpio_pin'])
                if 'i2c_address' in data and data['i2c_address']:
                    component.attributes['i2c_address'] = data['i2c_address']
                if 'i2c_bus' in data and data['i2c_bus'] is not None:
                    component.attributes['i2c_bus'] = str(data['i2c_bus'])
                if 'spi_bus' in data and data['spi_bus'] is not None:
                    component.attributes['spi_bus'] = str(data['spi_bus'])
                if 'spi_device' in data and data['spi_device'] is not None:
                    component.attributes['spi_device'] = str(data['spi_device'])
                
                break
        
        # Update the robot configuration in Viam
        robot.reconfigure_config(config)
        robot.close()
        
        return jsonify({
            'success': True,
            'message': 'Sensor pins updated in Viam',
            'sensor_name': sensor.name
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating sensor pins: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to update pins: {str(e)}'
        }), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')

