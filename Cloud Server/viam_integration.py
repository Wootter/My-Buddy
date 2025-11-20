# -*- coding: utf-8 -*-
"""
Viam Integration Module
Handles fetching sensor data from Viam robot and storing in database.
"""

from datetime import datetime
from extensions import db
from models import SensorData
import logging

logger = logging.getLogger(__name__)

# ==================== CONFIGURATION ====================
# Viam robot connection settings
VIAM_ROBOT_ADDRESS = "my-buddy-main.1zxw399cc5.viam.cloud"
VIAM_API_KEY = "v1wu2a2mu5lobgmmrkqypy6m2zhys78i"
VIAM_API_KEY_ID = "cd0b2909-909c-4061-809e-9876f5cb8b91"

# Sensor mapping: Viam component name → Flask sensor ID
VIAM_SENSORS = [
    {
        'viam_name': 'dht22_sensor',  # Actual component name from Viam
        'flask_sensor_id': 1,  # DHT22 Temperature
        'reading_key': 'temperature_celsius',
        'unit': '°C'
    },
    {
        'viam_name': 'dht22_sensor',  # Same sensor, different reading
        'flask_sensor_id': 2,  # DHT22 Humidity
        'reading_key': 'humidity_percent',
        'unit': '%'
    },
    {
        'viam_name': 'VEML7700',  # Actual component name from Viam
        'flask_sensor_id': 3,  # VEML7700 Light
        'reading_key': 'lux',
        'unit': 'lux'
    },
    {
        'viam_name': 'MH-SR602',  # Actual component name from Viam
        'flask_sensor_id': 4,  # MH-SR602 Motion
        'reading_key': 'motion_detected',
        'unit': 'bool'
    }
]


async def _fetch_viam_data_async():
    """Async function to fetch data from Viam robot."""
    from viam.robot.client import RobotClient
    from viam.components.sensor import Sensor as ViamSensor
    
    logger.info(f"[{datetime.now()}] Fetching sensor data from Viam...")
    
    # Connect to Viam robot
    opts = RobotClient.Options.with_api_key(
        api_key=VIAM_API_KEY,
        api_key_id=VIAM_API_KEY_ID
    )
    robot = await RobotClient.at_address(VIAM_ROBOT_ADDRESS, opts)
    
    timestamp = datetime.utcnow()
    readings_saved = 0
    
    try:
        # Fetch data from each sensor
        for sensor_config in VIAM_SENSORS:
            try:
                # Get the sensor component
                sensor = ViamSensor.from_robot(robot, sensor_config['viam_name'])
                sensor_readings = await sensor.get_readings()
                
                # Extract the specific reading
                reading_key = sensor_config['reading_key']
                if reading_key in sensor_readings:
                    value = sensor_readings[reading_key]
                    
                    # Convert boolean to float for storage
                    if isinstance(value, bool):
                        value = 1.0 if value else 0.0
                    else:
                        value = float(value)
                    
                    # Store in database
                    data_point = SensorData(
                        sensor_id=sensor_config['flask_sensor_id'],
                        timestamp=timestamp,
                        value=value,
                        unit=sensor_config['unit']
                    )
                    db.session.add(data_point)
                    readings_saved += 1
                    
                    logger.info(f"  ✓ {sensor_config['viam_name']}: {value} {sensor_config['unit']}")
                else:
                    logger.warning(f"  ⚠ {sensor_config['viam_name']}: Key '{reading_key}' not found in {list(sensor_readings.keys())}")
                    
            except Exception as e:
                logger.error(f"  ✗ {sensor_config['viam_name']}: {e}")
        
        # Commit all readings
        db.session.commit()
        logger.info(f"✓ Stored {readings_saved}/{len(VIAM_SENSORS)} sensor readings")
        
    finally:
        await robot.close()
    
    return readings_saved


def fetch_and_store_sensor_data():
    """
    Fetch sensor data from Viam and store in database.
    Called by scheduler every hour.
    """
    try:
        import asyncio
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            readings_saved = loop.run_until_complete(_fetch_viam_data_async())
            return readings_saved > 0
        finally:
            loop.close()
        
    except ImportError:
        logger.error("viam-sdk not installed. Install with: pip install viam-sdk")
        return False
    except Exception as e:
        logger.error(f"Failed to fetch Viam data: {e}")
        db.session.rollback()
        return False


async def _test_viam_connection_async():
    """Async test connection to Viam robot."""
    from viam.robot.client import RobotClient
    
    print(f"Testing connection to {VIAM_ROBOT_ADDRESS}...")
    
    opts = RobotClient.Options.with_api_key(
        api_key=VIAM_API_KEY,
        api_key_id=VIAM_API_KEY_ID
    )
    robot = await RobotClient.at_address(VIAM_ROBOT_ADDRESS, opts)
    
    try:
        print(f"✓ Connected successfully!")
        print(f"\nAvailable components:")
        
        # List all components
        resources = robot.resource_names
        for resource in resources:
            print(f"  - {resource}")
        
    finally:
        await robot.close()
    
    return True


def test_viam_connection():
    """Test connection to Viam robot (call this manually to verify setup)"""
    try:
        import asyncio
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_test_viam_connection_async())
            return True
        finally:
            loop.close()
        
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False


async def _get_robot_info_async():
    """Async function to get robot/device information."""
    from viam.robot.client import RobotClient
    
    opts = RobotClient.Options.with_api_key(
        api_key=VIAM_API_KEY,
        api_key_id=VIAM_API_KEY_ID
    )
    robot = await RobotClient.at_address(VIAM_ROBOT_ADDRESS, opts)
    
    try:
        # Get basic robot info
        robot_info = {
            'name': VIAM_ROBOT_ADDRESS.split('.')[0],  # Extract robot name from address
            'address': VIAM_ROBOT_ADDRESS,
            'status': 'Online',
            'components': len(robot.resource_names),
            'last_seen': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        }
        
        return robot_info
        
    finally:
        await robot.close()


def get_robot_info():
    """
    Get information about the connected Viam robot/Raspberry Pi.
    Returns dict with name, address, status, etc.
    """
    try:
        import asyncio
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_get_robot_info_async())
        finally:
            loop.close()
        
    except Exception as e:
        logger.error(f"Failed to get robot info: {e}")
        return {
            'name': VIAM_ROBOT_ADDRESS.split('.')[0],
            'address': VIAM_ROBOT_ADDRESS,
            'status': 'Offline',
            'components': 0,
            'last_seen': 'Never'
        }
