from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime, timedelta
import random
import json

app = Flask(__name__,
            static_url_path='/static',
            static_folder='static',
            template_folder='templates')

app.config['SECRET_KEY'] = 'dev-key-for-local-testing-only'

# Dummy user data
USERS = {
    'woudeelen@gmail.com': {
        'password': 'test123',
        'name': 'Wout Deelen',
        'username': 'Wootter',
        'email': 'woudeelen@gmail.com',
        'robot_name': 'My Buddy Bot',
        'created_at': '2025-01-15',
        'profile_picture': None,
        'bio': 'Robotics enthusiast and maker',
        'location': 'Netherlands',
        'preferences': {
            'theme': 'dark',
            'notifications': True,
            'data_refresh': 5
        }
    },
    'demo@example.com': {
        'password': 'demo123',
        'name': 'Demo User',
        'username': 'DemoUser',
        'email': 'demo@example.com',
        'robot_name': 'Demo Robot',
        'created_at': '2025-02-01',
        'profile_picture': None,
        'bio': 'Testing the platform',
        'location': 'USA',
        'preferences': {
            'theme': 'light',
            'notifications': False,
            'data_refresh': 10
        }
    }
}

# Robot configurations per user
ROBOT_CONFIGS = {
    'woudeelen@gmail.com': {
        'robot_id': 'buddy-robot-001',
        'robot_name': 'My Buddy Bot',
        'location': 'Living Room',
        'api_key': 'viam-api-key-xxxxx-xxxxx',
        'api_key_id': 'key-id-12345',
        'status': 'online',
        'last_seen': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'sensors': {
            'temperature': {
                'enabled': True,
                'pin': 'GPIO4',
                'model': 'DHT22',
                'update_interval': 5,
                'min_threshold': 15,
                'max_threshold': 30
            },
            'humidity': {
                'enabled': True,
                'pin': 'GPIO4',
                'model': 'DHT22',
                'update_interval': 5,
                'min_threshold': 20,
                'max_threshold': 80
            },
            'light': {
                'enabled': True,
                'pin': 'I2C',
                'model': 'VEML7700',
                'update_interval': 10,
                'min_threshold': 0,
                'max_threshold': 2000
            },
            'motion': {
                'enabled': True,
                'pin': 'GPIO17',
                'model': 'PIR SR602',
                'update_interval': 1,
                'sensitivity': 'high'
            }
        }
    },
    'demo@example.com': {
        'robot_id': 'demo-robot-002',
        'robot_name': 'Demo Robot',
        'location': 'Office',
        'api_key': 'viam-api-key-demo-xxxxx',
        'api_key_id': 'key-id-67890',
        'status': 'offline',
        'last_seen': (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
        'sensors': {
            'temperature': {
                'enabled': True,
                'pin': 'GPIO4',
                'model': 'DHT22',
                'update_interval': 10,
                'min_threshold': 18,
                'max_threshold': 28
            },
            'humidity': {
                'enabled': False,
                'pin': 'GPIO4',
                'model': 'DHT22',
                'update_interval': 10,
                'min_threshold': 30,
                'max_threshold': 70
            },
            'light': {
                'enabled': True,
                'pin': 'I2C',
                'model': 'VEML7700',
                'update_interval': 15,
                'min_threshold': 100,
                'max_threshold': 1500
            },
            'motion': {
                'enabled': False,
                'pin': 'GPIO17',
                'model': 'PIR SR602',
                'update_interval': 2,
                'sensitivity': 'medium'
            }
        }
    }
}

# Generate dummy sensor data
def generate_sensor_data(hours=24):
    data = []
    now = datetime.now()
    for i in range(hours * 12):  # Every 5 minutes
        timestamp = now - timedelta(minutes=i*5)
        temp = round(random.uniform(18, 28), 1)
        hum = round(random.uniform(30, 70), 1)
        data.append({
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'temperature': temp,
            'humidity': hum,
            'light': round(random.uniform(100, 1000), 0),
            'motion': random.choice([True, False]),
            'feels_like': round(temp + (hum / 100) * 2, 1)
        })
    return list(reversed(data))

SENSOR_DATA = generate_sensor_data()

# Activity log
ACTIVITY_LOG = [
    {'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'action': 'System started', 'user': 'System'},
    {'timestamp': (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S'), 'action': 'Sensor calibrated', 'user': 'woudeelen@gmail.com'},
    {'timestamp': (datetime.now() - timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S'), 'action': 'Configuration updated', 'user': 'woudeelen@gmail.com'},
]

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user = USERS.get(session['user'])
    robot_config = ROBOT_CONFIGS.get(session['user'], {})
    latest_data = SENSOR_DATA[-1] if SENSOR_DATA else None
    
    return render_template('home.html', 
                         user=user, 
                         current_user=user,
                         robot_config=robot_config,
                         sensor_data=latest_data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if email in USERS and USERS[email]['password'] == password:
            session['user'] = email
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name', 'New User')
        
        if email in USERS:
            flash('Email already registered', 'error')
        else:
            USERS[email] = {
                'password': password,
                'name': name,
                'username': email.split('@')[0],
                'email': email,
                'robot_name': 'My Buddy',
                'created_at': datetime.now().strftime('%Y-%m-%d')
            }
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user = USERS.get(session['user'])
    
    if request.method == 'POST':
        action = request.form.get('action', 'update_profile')
        
        if action == 'update_profile':
            # Update user profile
            user['name'] = request.form.get('name', user['name'])
            user['username'] = request.form.get('username', user['username'])
            user['email'] = request.form.get('email', user['email'])
            user['bio'] = request.form.get('bio', user.get('bio', ''))
            user['location'] = request.form.get('location', user.get('location', ''))
            flash('Profile updated successfully!', 'success')
            
        elif action == 'change_password':
            old_password = request.form.get('old_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if old_password == user['password']:
                if new_password == confirm_password:
                    user['password'] = new_password
                    flash('Password changed successfully!', 'success')
                else:
                    flash('New passwords do not match!', 'error')
            else:
                flash('Current password is incorrect!', 'error')
                
        elif action == 'update_preferences':
            if 'preferences' not in user:
                user['preferences'] = {}
            user['preferences']['theme'] = request.form.get('theme', 'dark')
            user['preferences']['notifications'] = request.form.get('notifications') == 'on'
            user['preferences']['data_refresh'] = int(request.form.get('data_refresh', 5))
            flash('Preferences updated!', 'success')
            
        elif action == 'delete_account':
            # In a real app, you'd delete the account
            flash('Account deletion requested (demo only)', 'warning')
    
    robot_config = ROBOT_CONFIGS.get(session['user'], {})
    
    return render_template('profile.html', 
                         user=user, 
                         current_user=user,
                         robot_config=robot_config,
                         activity_log=ACTIVITY_LOG[:10])

@app.route('/data')
def data():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user = USERS.get(session['user'])
    robot_config = ROBOT_CONFIGS.get(session['user'], {})
    
    # Get enabled sensors
    sensors = []
    charts = []
    
    if robot_config and 'sensors' in robot_config:
        for sensor_name, sensor_config in robot_config['sensors'].items():
            if sensor_config.get('enabled', False):
                sensors.append({
                    'name': sensor_name.capitalize(),
                    'type': sensor_config.get('model', 'Unknown'),
                    'status': 'active'
                })
                
                # Prepare chart data
                chart_data = []
                for reading in SENSOR_DATA[-100:]:
                    if sensor_name in reading:
                        unit = ''
                        if sensor_name == 'temperature':
                            unit = '°C'
                        elif sensor_name == 'humidity':
                            unit = '%'
                        elif sensor_name == 'light':
                            unit = 'lux'
                        
                        chart_data.append({
                            'timestamp': reading['timestamp'],
                            'value': reading[sensor_name],
                            'unit': unit
                        })
                
                charts.append({
                    'name': sensor_name.capitalize(),
                    'type': sensor_config.get('model', 'Sensor'),
                    'data': chart_data
                })
    
    return render_template('data.html', 
                         user=user, 
                         current_user=user,
                         sensors=sensors,
                         charts=charts,
                         sensor_data=SENSOR_DATA[-100:])


@app.route('/api/sensor-data')
def api_sensor_data():
    """API endpoint for chart data"""
    limit = request.args.get('limit', 100, type=int)
    data = SENSOR_DATA[-limit:]
    
    return jsonify({
        'timestamps': [d['timestamp'] for d in data],
        'temperature': [d['temperature'] for d in data],
        'humidity': [d['humidity'] for d in data],
        'light': [d['light'] for d in data],
        'motion': [d['motion'] for d in data]
    })

@app.route('/configure', methods=['GET', 'POST'])
def configure():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user = USERS.get(session['user'])
    robot_config = ROBOT_CONFIGS.get(session['user'], {})
    
    if request.method == 'POST':
        action = request.form.get('action', 'update_config')
        
        if action == 'update_robot':
            robot_config['robot_name'] = request.form.get('robot_name', robot_config.get('robot_name'))
            robot_config['location'] = request.form.get('location', robot_config.get('location'))
            robot_config['api_key'] = request.form.get('api_key', robot_config.get('api_key'))
            robot_config['api_key_id'] = request.form.get('api_key_id', robot_config.get('api_key_id'))
            flash('Robot settings updated!', 'success')
            
        elif action == 'update_sensor':
            sensor_type = request.form.get('sensor_type')
            if sensor_type and sensor_type in robot_config.get('sensors', {}):
                sensor = robot_config['sensors'][sensor_type]
                sensor['enabled'] = request.form.get(f'{sensor_type}_enabled') == 'on'
                sensor['update_interval'] = int(request.form.get(f'{sensor_type}_interval', sensor.get('update_interval', 5)))
                sensor['min_threshold'] = float(request.form.get(f'{sensor_type}_min', sensor.get('min_threshold', 0)))
                sensor['max_threshold'] = float(request.form.get(f'{sensor_type}_max', sensor.get('max_threshold', 100)))
                if 'pin' in request.form:
                    sensor['pin'] = request.form.get('pin', sensor.get('pin'))
                flash(f'{sensor_type.capitalize()} sensor updated!', 'success')
        
        elif action == 'test_connection':
            # Simulate connection test
            robot_config['status'] = random.choice(['online', 'online', 'online', 'offline'])
            robot_config['last_seen'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if robot_config['status'] == 'online':
                flash('Connection test successful!', 'success')
            else:
                flash('Connection test failed!', 'error')
    
    return render_template('configure.html', 
                         user=user, 
                         current_user=user,
                         robot_config=robot_config)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        if email in USERS:
            flash('Password reset link sent to your email (demo only)', 'success')
        else:
            flash('Email not found', 'error')
    
    return render_template('forgot-password.html')

@app.route('/404')
def not_found():
    return render_template('404.html')

# Additional API endpoints
@app.route('/api/live-sensor')
def api_live_sensor():
    """Real-time sensor data endpoint"""
    latest = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'temperature': round(random.uniform(18, 28), 1),
        'humidity': round(random.uniform(30, 70), 1),
        'light': round(random.uniform(100, 1000), 0),
        'motion': random.choice([True, False])
    }
    SENSOR_DATA.append(latest)
    if len(SENSOR_DATA) > 1000:
        SENSOR_DATA.pop(0)
    return jsonify(latest)

@app.route('/api/robot-status')
def api_robot_status():
    """Robot status endpoint"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    robot_config = ROBOT_CONFIGS.get(session['user'], {})
    return jsonify({
        'status': robot_config.get('status', 'unknown'),
        'robot_name': robot_config.get('robot_name', 'Unknown'),
        'last_seen': robot_config.get('last_seen', 'Never'),
        'sensors_active': sum(1 for s in robot_config.get('sensors', {}).values() if s.get('enabled', False))
    })

@app.route('/api/export-data')
def api_export_data():
    """Export sensor data as JSON"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    return jsonify({
        'user': session['user'],
        'export_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'data': SENSOR_DATA[-1000:]  # Last 1000 readings
    })

@app.route('/api/statistics')
def api_statistics():
    """Get statistical summary of sensor data"""
    recent_data = SENSOR_DATA[-100:]
    
    temps = [d['temperature'] for d in recent_data]
    hums = [d['humidity'] for d in recent_data]
    lights = [d['light'] for d in recent_data]
    
    return jsonify({
        'temperature': {
            'current': temps[-1] if temps else 0,
            'average': round(sum(temps) / len(temps), 1) if temps else 0,
            'min': min(temps) if temps else 0,
            'max': max(temps) if temps else 0
        },
        'humidity': {
            'current': hums[-1] if hums else 0,
            'average': round(sum(hums) / len(hums), 1) if hums else 0,
            'min': min(hums) if hums else 0,
            'max': max(hums) if hums else 0
        },
        'light': {
            'current': lights[-1] if lights else 0,
            'average': round(sum(lights) / len(lights), 1) if lights else 0,
            'min': min(lights) if lights else 0,
            'max': max(lights) if lights else 0
        },
        'motion_events': sum(1 for d in recent_data if d.get('motion', False))
    })


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 My Buddy - Local Development Server")
    print("=" * 60)
    print("📱 Open your browser at: http://localhost:5000")
    print("🎨 Edit HTML/CSS/JS and refresh to see changes!")
    print("\n📝 Test Accounts:")
    print("   Email: woudeelen@gmail.com | Password: test123")
    print("   Email: demo@example.com | Password: demo123")
    print("\n🔧 Features:")
    print("   ✅ Login/Register/Logout")
    print("   ✅ Profile Management (password change, preferences)")
    print("   ✅ Live Sensor Data & Charts")
    print("   ✅ Robot Configuration (sensors, thresholds)")
    print("   ✅ API Endpoints (/api/sensor-data, /api/live-sensor, etc.)")
    print("   ✅ Activity Logging")
    print("   ✅ Data Export")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
