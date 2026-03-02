# -*- coding: utf-8 -*-
"""
Viam Integration Module
Queries cloud-stored sensor data via Viam Data Client API.
Polls every 10 seconds for live display and hourly for historical data.
"""

from datetime import datetime
from extensions import db, socketio
from models import SensorData, Sensor, Robot
import logging
from cryptography.fernet import InvalidToken

logger = logging.getLogger(__name__)

# Sensor mapping: sensor database table → sensor name & unit
VIAM_SENSORS = [
    {
        'database_name': 'DHT22',  # Table/sensor name in Viam
        'sensor_name': 'DHT22 Temperature',
        'column': 'temperature_celsius',
        'unit': '°C'
    },
    {
        'database_name': 'DHT22',
        'sensor_name': 'DHT22 Humidity',
        'column': 'humidity_percent',
        'unit': '%'
    },
    {
        'database_name': 'VEML7700',
        'sensor_name': 'VEML7700 Light',
        'column': 'lux',
        'unit': 'lux'
    },
    {
        'database_name': 'MH-SR602',
        'sensor_name': 'MH-SR602 Motion',
        'column': 'motion_detected',
        'unit': 'bool'
    }
]


def get_viam_data_client(api_key, api_key_id, org_id):
    """Create a Viam Data Client for querying cloud data."""
    try:
        from viam.app.data_client import DataClient
        return DataClient(
            api_key=api_key,
            api_key_id=api_key_id,
            org_id=org_id
        )
    except ImportError:
        logger.error("viam-sdk not installed. Install with: pip install viam-sdk")
        return None
    except Exception as e:
        logger.error(f"Failed to create Viam DataClient: {e}")
        return None


def fetch_live_sensor_data():
    """Fetch latest sensor readings for Socket.IO broadcast (runs every 10 seconds)."""
    try:
        robots = Robot.query.all()
        if not robots:
            return {}
        
        all_live_readings = {}
        
        for robot in robots:
            try:
                user_robot = robot.user_robots[0] if robot.user_robots else None
                if not user_robot:
                    continue
                
                org_id = getattr(robot, 'viam_org_id', None)
                if not org_id:
                    continue
                
                try:
                    api_key = user_robot.get_viam_api_key()
                    api_key_id = user_robot.get_viam_api_key_id()
                except InvalidToken:
                    continue
                
                client = get_viam_data_client(api_key, api_key_id, org_id)
                if not client:
                    continue
                
                robot_readings = _query_robot_latest_data(client, robot.id, robot.robot_name)
                if robot_readings:
                    all_live_readings.update(robot_readings)
                
            except Exception as e:
                logger.debug(f"[LIVE] Failed to fetch data for {robot.robot_name}: {e}")
        
        return all_live_readings
        
    except Exception as e:
        logger.error(f"[LIVE] Failed to fetch Viam live data: {e}")
        return {}


def _query_robot_latest_data(data_client, robot_id, robot_name):
    """Query latest sensor readings from Viam Data API."""
    try:
        robot_readings = {}
        timestamp = datetime.utcnow()
        
        for sensor_config in VIAM_SENSORS:
            try:
                sql_query = f"""
                SELECT {sensor_config['column']} 
                FROM {sensor_config['database_name']}
                WHERE robot_id = '{robot_id}'
                ORDER BY timestamp DESC
                LIMIT 1
                """
                
                results = data_client.tabular_data_by_sql(org_id=None, sql=sql_query)
                if results:
                    value = results[0].get(sensor_config['column'])
                    
                    if value is not None:
                        if isinstance(value, bool):
                            value = 1.0 if value else 0.0
                        else:
                            value = float(value)
                        
                        robot_readings[sensor_config['sensor_name']] = {
                            'value': value,
                            'unit': sensor_config['unit'],
                            'timestamp': timestamp.isoformat()
                        }
            
            except Exception as e:
                pass
        
        return robot_readings


def fetch_and_store_sensor_data():
    """Fetch latest readings and store in local database (runs hourly)."""
    try:
        robots = Robot.query.all()
        if not robots:
            return False
        
        total_readings = 0
        
        for robot in robots:
            try:
                user_robot = robot.user_robots[0] if robot.user_robots else None
                if not user_robot:
                    continue
                
                org_id = getattr(robot, 'viam_org_id', None)
                if not org_id:
                    continue
                
                try:
                    api_key = user_robot.get_viam_api_key()
                    api_key_id = user_robot.get_viam_api_key_id()
                except InvalidToken:
                    logger.error(f"Failed to decrypt credentials for robot: {robot.robot_name}")
                    continue
                
                logger.info(f"Fetching data for robot: {robot.robot_name}")
                client = get_viam_data_client(api_key, api_key_id, org_id)
                if not client:
                    continue
                
                readings = _query_and_store_robot_data(client, robot)
                total_readings += readings
                
            except Exception as e:
                logger.error(f"Failed to fetch data for {robot.robot_name}: {e}")
                db.session.rollback()
        
        if total_readings > 0:
            logger.info(f"✓ Stored {total_readings} sensor readings")
            logger.info("Emitting update_sensor_data event")
            socketio.emit('update_sensor_data', {'message': 'New sensor data available'})
        
        return total_readings > 0
        
    except Exception as e:
        logger.error(f"Failed to fetch Viam data: {e}")
        db.session.rollback()
        return False


def _query_and_store_robot_data(data_client, robot):
    """Query and store sensor readings to local database."""
    try:
        timestamp = datetime.utcnow()
        readings_stored = 0
        
        for sensor_config in VIAM_SENSORS:
            try:
                sensor = Sensor.query.filter_by(
                    robot_id=robot.id,
                    name=sensor_config['sensor_name']
                ).first()
                
                if not sensor:
                    sensor = Sensor(
                        robot_id=robot.id,
                        name=sensor_config['sensor_name'],
                        sensor_type='viam'
                    )
                    db.session.add(sensor)
                    db.session.flush()
                
                sql_query = f"""
                SELECT {sensor_config['column']} 
                FROM {sensor_config['database_name']}
                WHERE robot_id = '{robot.id}'
                ORDER BY timestamp DESC
                LIMIT 1
                """
                
                results = data_client.tabular_data_by_sql(org_id=None, sql=sql_query)
                
                if results:
                    value = results[0].get(sensor_config['column'])
                    
                    if value is not None:
                        if isinstance(value, bool):
                            value = 1.0 if value else 0.0
                        else:
                            value = float(value)
                        
                        data_point = SensorData(
                            sensor_id=sensor.id,
                            timestamp=timestamp,
                            value=value,
                            unit=sensor_config['unit']
                        )
                        db.session.add(data_point)
                        readings_stored += 1
                        logger.info(f"  ✓ {sensor_config['sensor_name']}: {value} {sensor_config['unit']}")
                
            except Exception as e:
                logger.error(f"  ✗ {sensor_config['sensor_name']}: {e}")
        
        if readings_stored > 0:
            db.session.commit()
            logger.info(f"✓ Stored {readings_stored}/{len(VIAM_SENSORS)} sensor readings for {robot.robot_name}")
        
        return readings_stored
        
    except Exception as e:
        logger.error(f"Failed to query and store data: {e}")
        db.session.rollback()
        return 0


