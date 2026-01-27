import asyncio
from viam.robot.client import RobotClient
from viam.components.sensor import Sensor as ViamSensor

# ------------------------
# CONFIG
# ------------------------

ROBOT_ADDRESS = "my-buddy-main.1zxw399cc5.viam.cloud"
API_KEY_ID = "1dd258cc-c05f-4c45-b81a-97731e419e2d"
API_KEY = "nole6vqgb2biwxn535oj1x38et903ihp"

# Map intents to Viam sensors and reading keys
INTENT_SENSOR_MAP = {
    "showTemperature": {"sensor_name": "DHT22", "reading_key": "temperature_celsius", "unit": "°C"},
    "showHumidity": {"sensor_name": "DHT22", "reading_key": "humidity_percent", "unit": "%"},
    "showLightIntensity": {"sensor_name": "VEML7700", "reading_key": "lux", "unit": "lux"},
}

# ------------------------
# FETCH SENSOR
# ------------------------
async def fetch_sensor_reading(robot, intent):
    cfg = INTENT_SENSOR_MAP.get(intent)
    if not cfg:
        return None

    sensor_name = cfg["sensor_name"]
    reading_key = cfg["reading_key"]
    unit = cfg["unit"]

    try:
        sensor = ViamSensor.from_robot(robot, sensor_name)  # DO NOT await
        readings = await sensor.get_readings()              # MUST await
        if readings and reading_key in readings:
            return readings[reading_key], unit
        else:
            return None, unit
    except Exception as e:
        print(f"Error fetching {sensor_name}: {e}")
        return None, unit

# ------------------------
# INTENT HANDLER
# ------------------------
async def handle_intent(intent, slots, robot):
    room = slots.get("room", "inside")  # fallback
    value, unit = await fetch_sensor_reading(robot, intent)
    if value is not None:
        print(f"{intent} in {room}: {value} {unit}")
    else:
        print(f"No data available for {intent} in {room}")

# ------------------------
# MAIN LOOP EXAMPLE
# ------------------------
async def main():
    opts = RobotClient.Options.with_api_key(api_key=API_KEY, api_key_id=API_KEY_ID)
    robot = await RobotClient.at_address(ROBOT_ADDRESS, opts)
    print("Connected to robot:", ROBOT_ADDRESS)

    try:
        # Example test calls (simulate intents)
        await handle_intent("showTemperature", {"room": "room"}, robot)
        await handle_intent("showHumidity", {"room": "inside"}, robot)
        await handle_intent("showLightIntensity", {"room": "room"}, robot)

    finally:
        await robot.close()
        print("Disconnected from robot")

if __name__ == "__main__":
    asyncio.run(main())
