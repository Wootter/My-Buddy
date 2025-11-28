# -*- coding: utf-8 -*-
"""
Viam Integration Module
Handles fetching sensor data from Viam robot and storing in database.
"""

from datetime import datetime
from extensions import db
from models import SensorData, Sensor, Robot
import logging

logger = logging.getLogger(__name__)

# Sensor mapping: Viam component name → sensor name & reading key
VIAM_SENSORS = [
    {
        'viam_name': 'dht22_sensor',
        'sensor_name': 'DHT22 Temperature',
        'reading_key': 'temperature_celsius',
        'unit': '°C'
    },
    {
        'viam_name': 'dht22_sensor',
        'sensor_name': 'DHT22 Humidity',
        'reading_key': 'humidity_percent',
        'unit': '%'
    },
    {
        'viam_name': 'VEML7700',
        'sensor_name': 'VEML7700 Light',
        'reading_key': 'lux',
        'unit': 'lux'
    },
    {
        'viam_name': 'MH-SR602',
        'sensor_name': 'MH-SR602 Motion',
        'reading_key': 'motion_detected',
        'unit': 'bool'
    }
]


async def _fetch_viam_data_async(robot_id, api_key, api_key_id, robot_address):
    """Async function to fetch data from Viam robot."""
    from viam.robot.client import RobotClient
    from viam.components.sensor import Sensor as ViamSensor
    
    logger.info(f"[{datetime.now()}] Fetching sensor data from Viam...")
    
    # Connect to Viam robot
    opts = RobotClient.Options.with_api_key(
        api_key=api_key,
        api_key_id=api_key_id
    )
    robot = await RobotClient.at_address(robot_address, opts)
    
    timestamp = datetime.utcnow()
    readings_saved = 0
    
    try:
        # Fetch data from each sensor
        for sensor_config in VIAM_SENSORS:
            try:
                # Get or create sensor in database
                sensor = Sensor.query.filter_by(
                    robot_id=robot_id,
                    name=sensor_config['sensor_name']
                ).first()
                
                if not sensor:
                    # Create sensor if it doesn't exist
                    sensor = Sensor(
                        robot_id=robot_id,
                        name=sensor_config['sensor_name'],
                        sensor_type='viam'
                    )
                    db.session.add(sensor)
                    db.session.flush()
                
                # Get the sensor component from Viam
                viam_sensor = ViamSensor.from_robot(robot, sensor_config['viam_name'])
                sensor_readings = await viam_sensor.get_readings()
                
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
                        sensor_id=sensor.id,
                        timestamp=timestamp,
                        value=value,
                        unit=sensor_config['unit']
                    )
                    db.session.add(data_point)
                    readings_saved += 1
                    
                    logger.info(f"  ✓ {sensor_config['sensor_name']}: {value} {sensor_config['unit']}")
                else:
                    logger.warning(f"  ⚠ {sensor_config['sensor_name']}: Key '{reading_key}' not found in {list(sensor_readings.keys())}")
                    
            except Exception as e:
                logger.error(f"  ✗ {sensor_config['sensor_name']}: {e}")
        
        # Commit all readings
        db.session.commit()
        logger.info(f"✓ Stored {readings_saved}/{len(VIAM_SENSORS)} sensor readings")
        
    finally:
        await robot.close()
    
    return readings_saved


def fetch_and_store_sensor_data():
    """
    Fetch sensor data from Viam for all connected user robots.
    Called by scheduler every hour.
    """
    try:
        import asyncio
        
        # Get all robots that have been connected by users
        robots = Robot.query.all()
        
        if not robots:
            logger.info("No robots connected yet.")
            return False
        
        total_readings = 0
        
        # Fetch data for each robot
        for robot in robots:
            try:
                # Get a user's credentials for this robot to test connection
                user_robot = robot.user_robots[0] if robot.user_robots else None
                
                if not user_robot:
                    logger.warning(f"Robot {robot.robot_name} has no users connected")
                    continue
                
                logger.info(f"Fetching data for robot: {robot.robot_name}")
                
                # Run the async function
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    readings = loop.run_until_complete(_fetch_viam_data_async(
                        robot_id=robot.id,
                        api_key=user_robot.viam_api_key,
                        api_key_id=user_robot.viam_api_key_id,
                        robot_address=robot.viam_robot_address
                    ))
                    total_readings += readings
                finally:
                    loop.close()
                    
            except Exception as e:
                logger.error(f"Failed to fetch data for {robot.robot_name}: {e}")
                db.session.rollback()
        
        return total_readings > 0
        
    except ImportError:
        logger.error("viam-sdk not installed. Install with: pip install viam-sdk")
        return False
    except Exception as e:
        logger.error(f"Failed to fetch Viam data: {e}")
        db.session.rollback()
        return False


async def _test_viam_connection_async(api_key, api_key_id, robot_address):
    """Async test connection to Viam robot."""
    from viam.robot.client import RobotClient
    from viam.components.sensor import Sensor as ViamSensor
    
    print(f"Testing connection to {robot_address}...")
    
    opts = RobotClient.Options.with_api_key(
        api_key=api_key,
        api_key_id=api_key_id
    )
    robot = await RobotClient.at_address(robot_address, opts)
    
    try:
        print(f"✓ Connected successfully!")
        print(f"\nAvailable components:")
        
        # List all components
        resources = robot.resource_names
        for resource in resources:
            print(f"  - {resource}")
        
        # Test DHT22 sensor if available
        print(f"\nTesting sensors:")
        try:
            dht = ViamSensor.from_robot(robot, "dht22_sensor")
            readings = await dht.get_readings()
            print(f"✓ DHT22: {readings}")
        except Exception as e:
            print(f"⚠ DHT22: {e}")
        
        # Test VEML7700 if available
        try:
            veml = ViamSensor.from_robot(robot, "VEML7700")
            readings = await veml.get_readings()
            print(f"✓ VEML7700: {readings}")
        except Exception as e:
            print(f"⚠ VEML7700: {e}")
        
        # Test MH-SR602 if available
        try:
            motion = ViamSensor.from_robot(robot, "MH-SR602")
            readings = await motion.get_readings()
            print(f"✓ MH-SR602: {readings}")
        except Exception as e:
            print(f"⚠ MH-SR602: {e}")
        
    finally:
        await robot.close()
    
    return True


def test_viam_connection(api_key, api_key_id, robot_address):
    """Test connection to Viam robot (call this manually to verify setup)"""
    try:
        import asyncio
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_test_viam_connection_async(api_key, api_key_id, robot_address))
            return True
        finally:
            loop.close()
        
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False


async def _get_robot_info_async(api_key, api_key_id, robot_address):
    """Async function to get robot/device information."""
    from viam.robot.client import RobotClient
    
    opts = RobotClient.Options.with_api_key(
        api_key=api_key,
        api_key_id=api_key_id
    )
    robot = await RobotClient.at_address(robot_address, opts)
    
    try:
        # Get basic robot info
        robot_info = {
            'name': robot_address.split('.')[0],
            'address': robot_address,
            'status': 'Online',
            'components': len(robot.resource_names),
            'last_seen': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        }
        
        return robot_info
        
    finally:
        await robot.close()


def get_robot_info(api_key, api_key_id, robot_address):
    """
    Get information about the connected Viam robot/Raspberry Pi.
    Returns dict with name, address, status, etc.
    """
    try:
        import asyncio
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_get_robot_info_async(api_key, api_key_id, robot_address))
        finally:
            loop.close()
        
    except Exception as e:
        logger.error(f"Failed to get robot info: {e}")
        robot_name = robot_address.split('.')[0] if robot_address else 'Unknown'
        return {
            'name': robot_name,
            'address': robot_address,
            'status': 'Offline',
            'components': 0,
            'last_seen': 'Never'
        }
