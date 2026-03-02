# -*- coding: utf-8 -*-
"""
Viam Integration Module
Reads live sensor values from connected Viam robots and optionally stores them.
"""

from datetime import datetime
import asyncio
import logging

from cryptography.fernet import InvalidToken

from extensions import db, socketio
from models import SensorData, Sensor, Robot

logger = logging.getLogger(__name__)


VIAM_SENSORS = [
    {
        'component_name': 'dht22_sensor',
        'sensor_name': 'DHT22 Temperature',
        'reading_key': 'temperature_celsius',
        'unit': '°C'
    },
    {
        'component_name': 'dht22_sensor',
        'sensor_name': 'DHT22 Humidity',
        'reading_key': 'humidity_percent',
        'unit': '%'
    },
    {
        'component_name': 'VEML7700',
        'sensor_name': 'VEML7700 Light',
        'reading_key': 'lux',
        'unit': 'lux'
    },
    {
        'component_name': 'MH-SR602',
        'sensor_name': 'MH-SR602 Motion',
        'reading_key': 'motion_detected',
        'unit': 'bool'
    }
]


def _run_async(coro):
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


def _to_float(value):
    if value is None:
        return None

    if isinstance(value, bool):
        return 1.0 if value else 0.0

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


async def _connect_robot_async(api_key, api_key_id, robot_address):
    from viam.robot.client import RobotClient

    opts = RobotClient.Options.with_api_key(
        api_key=api_key,
        api_key_id=api_key_id,
    )
    return await RobotClient.at_address(robot_address, opts)


async def get_viam_data_client_async(api_key, api_key_id, org_id=None, robot_address=None):
    """Backward-compatible helper that returns a connected RobotClient instance."""
    if not robot_address:
        raise ValueError("robot_address is required")
    return await _connect_robot_async(api_key, api_key_id, robot_address)


def get_viam_data_client(api_key, api_key_id, org_id=None, robot_address=None):
    """Synchronous wrapper for backward compatibility."""
    try:
        return _run_async(get_viam_data_client_async(api_key, api_key_id, org_id, robot_address))
    except Exception as exc:
        logger.error("[VIAM] Failed to create RobotClient: %s", exc)
        return None


async def _query_robot_latest_data_async(api_key, api_key_id, robot_address, robot_name):
    from viam.components.sensor import Sensor as ViamSensor

    robot_client = None
    readings = {}
    timestamp = datetime.utcnow().isoformat()

    try:
        robot_client = await _connect_robot_async(api_key, api_key_id, robot_address)

        for sensor_config in VIAM_SENSORS:
            sensor_name = sensor_config['sensor_name']
            component_name = sensor_config['component_name']
            reading_key = sensor_config['reading_key']

            try:
                sensor = ViamSensor.from_robot(robot_client, component_name)
                raw_readings = await sensor.get_readings()
                raw_value = raw_readings.get(reading_key)
                value = _to_float(raw_value)

                if value is None:
                    continue

                readings[sensor_name] = {
                    'value': value,
                    'unit': sensor_config['unit'],
                    'timestamp': timestamp,
                }
            except Exception as sensor_exc:
                logger.debug(
                    "[VIAM] Robot %s - failed reading %s (%s): %s",
                    robot_name,
                    sensor_name,
                    component_name,
                    sensor_exc,
                )

        return readings
    finally:
        if robot_client is not None:
            try:
                await robot_client.close()
            except Exception:
                pass


def fetch_live_sensor_data():
    """Fetch latest sensor readings for Socket.IO broadcast."""
    try:
        robots = Robot.query.all()
        if not robots:
            return {}

        all_live_readings = {}

        for robot in robots:
            user_robot = robot.user_robots[0] if robot.user_robots else None
            if not user_robot:
                continue

            try:
                api_key = user_robot.get_viam_api_key()
                api_key_id = user_robot.get_viam_api_key_id()
            except InvalidToken:
                logger.error("[LIVE] Failed to decrypt credentials for robot: %s", robot.robot_name)
                continue

            try:
                robot_readings = _run_async(
                    _query_robot_latest_data_async(
                        api_key=api_key,
                        api_key_id=api_key_id,
                        robot_address=robot.viam_robot_address,
                        robot_name=robot.robot_name,
                    )
                )
            except Exception as exc:
                logger.error("[LIVE] Failed fetching %s: %s", robot.robot_name, exc)
                continue

            if robot_readings:
                all_live_readings.update(robot_readings)

        return all_live_readings
    except Exception as exc:
        logger.error("[LIVE] Fatal error in fetch_live_sensor_data: %s", exc, exc_info=True)
        return {}


def _get_or_create_sensor(robot_id, sensor_name):
    sensor = Sensor.query.filter_by(robot_id=robot_id, name=sensor_name).first()
    if sensor:
        return sensor

    sensor = Sensor(
        robot_id=robot_id,
        name=sensor_name,
        sensor_type='viam',
    )
    db.session.add(sensor)
    db.session.flush()
    return sensor


def _store_robot_readings(robot, readings):
    stored = 0

    for sensor_name, reading in readings.items():
        value = _to_float(reading.get('value'))
        if value is None:
            continue

        sensor = _get_or_create_sensor(robot.id, sensor_name)
        data_point = SensorData(
            sensor_id=sensor.id,
            timestamp=datetime.utcnow(),
            value=value,
            unit=reading.get('unit') or '',
        )
        db.session.add(data_point)
        stored += 1

    return stored


def fetch_and_store_sensor_data():
    """Fetch latest readings and store in local database."""
    try:
        robots = Robot.query.all()
        if not robots:
            return False

        total_readings = 0

        for robot in robots:
            user_robot = robot.user_robots[0] if robot.user_robots else None
            if not user_robot:
                continue

            try:
                api_key = user_robot.get_viam_api_key()
                api_key_id = user_robot.get_viam_api_key_id()
            except InvalidToken:
                logger.error("[STORE] Failed to decrypt credentials for robot: %s", robot.robot_name)
                continue

            try:
                readings = _run_async(
                    _query_robot_latest_data_async(
                        api_key=api_key,
                        api_key_id=api_key_id,
                        robot_address=robot.viam_robot_address,
                        robot_name=robot.robot_name,
                    )
                )
                total_readings += _store_robot_readings(robot, readings)
                db.session.commit()
            except Exception as exc:
                db.session.rollback()
                logger.error("[STORE] Failed to store data for %s: %s", robot.robot_name, exc)

        if total_readings > 0:
            socketio.emit('update_sensor_data', {'message': 'New sensor data available'})
            logger.info("✓ Stored %s sensor readings", total_readings)

        return total_readings > 0
    except Exception as exc:
        db.session.rollback()
        logger.error("[STORE] Fatal error in fetch_and_store_sensor_data: %s", exc, exc_info=True)
        return False


def _test_viam_connection_async(api_key, api_key_id, robot_address):
    return _query_robot_latest_data_async(
        api_key=api_key,
        api_key_id=api_key_id,
        robot_address=robot_address,
        robot_name=robot_address,
    )


def test_viam_connection(api_key, api_key_id, robot_address):
    """Simple connectivity/readings test used by /api/viam/test."""
    try:
        print(f"Connecting to robot: {robot_address}")
        readings = _run_async(_test_viam_connection_async(api_key, api_key_id, robot_address))

        if not readings:
            print("Connected, but no sensor readings were returned.")
            return False

        print(f"Connected successfully. Retrieved {len(readings)} sensor readings:")
        for sensor_name, reading in readings.items():
            print(f" - {sensor_name}: {reading['value']} {reading['unit']}")

        return True
    except Exception as exc:
        print(f"Connection failed: {exc}")
        logger.error("[TEST] test_viam_connection failed: %s", exc, exc_info=True)
        return False


