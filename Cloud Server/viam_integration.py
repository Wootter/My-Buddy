# -*- coding: utf-8 -*-
"""
Viam Integration Module
Handles fetching sensor data from Viam robot and storing in database.
"""

from datetime import datetime
from extensions import db, socketio
from models import SensorData, Sensor, Robot
import logging
import traceback
import nest_asyncio
from cryptography.fernet import InvalidToken

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

logger = logging.getLogger(__name__)

# Sensor mapping: Viam component name → sensor name & reading key
# Based on your DHT22 module: https://github.com/Wootter/viam-dht22-module
VIAM_SENSORS = [
    {
        'viam_name': 'DHT22',  # Updated to match your config
        'sensor_name': 'DHT22 Temperature',
        'reading_key': 'temperature_celsius',
        'unit': '°C'
    },
    {
        'viam_name': 'DHT22',  # Updated to match your config
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
    
    # List all available components for debugging
    logger.info(f"Available components in robot:")
    for resource in robot.resource_names:
        logger.info(f"  - {resource}")
    
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
                
                try:
                    # Get the sensor component from Viam
                    logger.info(f"  Attempting to get sensor component: {sensor_config['viam_name']}")
                    viam_sensor = ViamSensor.from_robot(robot, sensor_config['viam_name'])
                    logger.info(f"  Got sensor object: {type(viam_sensor)}")
                    
                    sensor_readings = await viam_sensor.get_readings()
                    logger.info(f"  DEBUG {sensor_config['sensor_name']}: Raw readings = {sensor_readings}")
                    
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
                        
                except Exception as sensor_error:
                    # Check if it's a component not found error
                    if "not found" in str(sensor_error).lower() or "component" in str(sensor_error).lower():
                        logger.error(f"  ✗ {sensor_config['sensor_name']}: Component '{sensor_config['viam_name']}' not found in robot")
                        logger.error(f"    This usually means the module isn't loaded or component isn't configured")
                    else:
                        logger.error(f"  ✗ {sensor_config['sensor_name']}: Sensor error - {sensor_error}")
                    raise sensor_error
                    
            except Exception as e:
                logger.error(f"  ✗ {sensor_config['sensor_name']}: {type(e).__name__}: {e}")
                # Don't log full traceback for expected component errors
                if "not found" not in str(e).lower():
                    import traceback
                    logger.error(f"  ✗ {sensor_config['sensor_name']} Full traceback: {traceback.format_exc()}")
        
        # Commit all readings
        db.session.commit()
        logger.info(f"✓ Stored {readings_saved}/{len(VIAM_SENSORS)} sensor readings")
        
    finally:
        await robot.close()
    
    return readings_saved


async def _fetch_viam_data_async_live(robot_id, api_key, api_key_id, robot_address):
    """Async function to fetch LIVE data from Viam robot (without saving to database)."""
    from viam.robot.client import RobotClient
    from viam.components.sensor import Sensor as ViamSensor
    
    logger.debug(f"[LIVE] Fetching sensor data from Viam...")
    
    # Connect to Viam robot
    opts = RobotClient.Options.with_api_key(
        api_key=api_key,
        api_key_id=api_key_id
    )
    robot = await RobotClient.at_address(robot_address, opts)
    
    timestamp = datetime.utcnow()
    live_readings = {}
    
    try:
        # Fetch data from each sensor
        for sensor_config in VIAM_SENSORS:
            try:
                try:
                    viam_sensor = ViamSensor.from_robot(robot, sensor_config['viam_name'])
                    sensor_readings = await viam_sensor.get_readings()
                    
                    reading_key = sensor_config['reading_key']
                    if reading_key in sensor_readings:
                        value = sensor_readings[reading_key]
                        
                        # Convert boolean to float for display
                        if isinstance(value, bool):
                            value = 1.0 if value else 0.0
                        else:
                            value = float(value)
                        
                        # Store in live_readings dict (NOT in database)
                        live_readings[sensor_config['sensor_name']] = {
                            'value': value,
                            'unit': sensor_config['unit'],
                            'timestamp': timestamp.isoformat()
                        }
                        
                        logger.debug(f"  [LIVE] {sensor_config['sensor_name']}: {value} {sensor_config['unit']}")
                    else:
                        logger.debug(f"  [LIVE] {sensor_config['sensor_name']}: Key '{reading_key}' not found")
                        
                except Exception as sensor_error:
                    logger.debug(f"  [LIVE] {sensor_config['sensor_name']}: {type(sensor_error).__name__}")
                    
            except Exception as e:
                logger.debug(f"  [LIVE] {sensor_config['sensor_name']}: {e}")
        
    finally:
        await robot.close()
    
    return live_readings


def fetch_live_sensor_data():
    """
    Fetch LIVE sensor data from Viam for all connected user robots.
    Does NOT save to database - only returns for Socket.IO broadcast.
    Called by scheduler every 5 seconds.
    """
    try:
        import asyncio
        
        # Get all robots that have been connected by users
        robots = Robot.query.all()
        
        if not robots:
            logger.debug("[LIVE] No robots connected yet.")
            return {}
        
        all_live_readings = {}
        
        # Fetch data for each robot
        for robot in robots:
            try:
                # Get a user's credentials for this robot
                user_robot = robot.user_robots[0] if robot.user_robots else None
                
                if not user_robot:
                    logger.debug(f"[LIVE] Robot {robot.robot_name} has no users connected")
                    continue
                
                # Run the async function
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    readings = loop.run_until_complete(_fetch_viam_data_async_live(
                        robot_id=robot.id,
                        api_key=user_robot.get_viam_api_key(),
                        api_key_id=user_robot.get_viam_api_key_id(),
                        robot_address=robot.viam_robot_address
                    ))
                    all_live_readings.update(readings)
                finally:
                    loop.close()
            
            except InvalidToken:
                logger.debug(f"[LIVE] Failed to decrypt credentials for robot: {robot.robot_name}")
                
            except Exception as e:
                logger.debug(f"[LIVE] Failed to fetch data for {robot.robot_name}: {e}")
        
        return all_live_readings
        
    except ImportError:
        logger.error("[LIVE] viam-sdk not installed. Install with: pip install viam-sdk")
        return {}
    except Exception as e:
        logger.error(f"[LIVE] Failed to fetch Viam live data: {e}")
        return {}


def fetch_and_store_sensor_data():
    """
    Fetch sensor data from Viam for all connected user robots.
    Called by scheduler every hour at xx:00.
    Data is SAVED to database for graphs.
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
                        api_key=user_robot.get_viam_api_key(),
                        api_key_id=user_robot.get_viam_api_key_id(),
                        robot_address=robot.viam_robot_address
                    ))
                    total_readings += readings
                finally:
                    loop.close()
            
            except InvalidToken:
                logger.error(f"Failed to decrypt credentials for robot: {robot.robot_name}")
                logger.error("Encryption key mismatch. Please re-enter robot credentials in the web interface.")
                
            except Exception as e:
                logger.error(f"Failed to fetch data for {robot.robot_name}: {e}")
                logger.error(traceback.format_exc())
                db.session.rollback()
        
        if total_readings > 0:
            logger.info("Emitting update_sensor_data event")
            socketio.emit('update_sensor_data', {'message': 'New sensor data available'})
        
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
