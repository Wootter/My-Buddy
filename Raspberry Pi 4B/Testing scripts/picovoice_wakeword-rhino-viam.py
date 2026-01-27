import time
import asyncio
from viam.robot.client import RobotClient
from viam.components.sensor import Sensor as ViamSensor
from pvrecorder import PvRecorder
import pvporcupine
import pvrhino

# ------------------------
# VIAM CONFIG
# ------------------------
ROBOT_ADDRESS = "my-buddy-main.1zxw399cc5.viam.cloud"
API_KEY_ID = "1dd258cc-c05f-4c45-b81a-97731e419e2d"
API_KEY = "nole6vqgb2biwxn535oj1x38et903ihp"

INTENT_SENSOR_MAP = {
    "showTemperature": {"sensor_name": "DHT22", "reading_key": "temperature_celsius", "unit": "°C"},
    "showHumidity": {"sensor_name": "DHT22", "reading_key": "humidity_percent", "unit": "%"},
    "showLightIntensity": {"sensor_name": "VEML7700", "reading_key": "lux", "unit": "lux"},
}

# ------------------------
# PORCUPINE / RHINO CONFIG
# ------------------------
ACCESS_KEY = 'cjmNT4hfxmJbe4vq5GRB6UAYw53HP9k7skrEAedIHmx1CllZn8W14Q=='
KEYWORD_PATH = 'Hey-buddy_en_raspberry-pi_v4_0_0.ppn'
CONTEXT_PATH = 'My-Buddy_en_raspberry-pi_v4_0_0.rhn'
USB_MIC_INDEX = 2
WAKEWORD_COOLDOWN = 300  # 5 minutes in seconds

# ------------------------
# VIAM SENSOR HELPERS
# ------------------------
async def fetch_sensor_reading(robot, intent):
    cfg = INTENT_SENSOR_MAP.get(intent)
    if not cfg:
        return None, None
    sensor_name, reading_key, unit = cfg["sensor_name"], cfg["reading_key"], cfg["unit"]
    try:
        sensor = ViamSensor.from_robot(robot, sensor_name)
        readings = await sensor.get_readings()
        return readings.get(reading_key), unit
    except Exception as e:
        print(f"Error fetching {sensor_name}: {e}")
        return None, unit

async def handle_sensor_intent(intent, slots, robot):
    room = slots.get("room", "inside")
    value, unit = await fetch_sensor_reading(robot, intent)
    if value is not None:
        print(f"{intent} in {room}: {value} {unit}")
    else:
        print(f"No data for {intent} in {room}")

# ------------------------
# OTHER INTENT HANDLER
# ------------------------
def handle_other_intent(intent, slots):
    if intent == "turnLight":
        print(f"Turning {slots.get('state')} light in {slots.get('room')}")
    elif intent == "setTimer":
        print(f"Setting timer for {slots.get('duration')}")
    else:
        print("Unknown intent:", intent)

# ------------------------
# MAIN LOOP
# ------------------------
async def main():
    # Connect to Viam
    opts = RobotClient.Options.with_api_key(api_key=API_KEY, api_key_id=API_KEY_ID)
    robot = await RobotClient.at_address(ROBOT_ADDRESS, opts)
    print("Connected to robot")

    # Init wake word and intent detection
    porcupine = pvporcupine.create(access_key=ACCESS_KEY, keyword_paths=[KEYWORD_PATH])
    rhino = pvrhino.create(access_key=ACCESS_KEY, context_path=CONTEXT_PATH)
    recorder = PvRecorder(device_index=USB_MIC_INDEX, frame_length=porcupine.frame_length)
    recorder.start()

    last_trigger = 0
    print("Listening for wake word...")

    try:
        while True:
            pcm = recorder.read()
            keyword_index = porcupine.process(pcm)

            # Check cooldown
            now = time.time()
            if keyword_index >= 0 and now - last_trigger >= WAKEWORD_COOLDOWN:
                last_trigger = now
                print("Wake word detected!")
                print("Listening for command...")

                rhino_activated = True
                while rhino_activated:
                    pcm_intent = recorder.read()
                    is_finalized = rhino.process(pcm_intent)
                    if is_finalized:
                        inference = rhino.get_inference()
                        intent, slots = inference.intent, inference.slots
                        print("Intent:", intent, "Slots:", slots)

                        if intent in INTENT_SENSOR_MAP:
                            await handle_sensor_intent(intent, slots, robot)
                        else:
                            handle_other_intent(intent, slots)

                        rhino_activated = False
                        print("Listening for wake word...")
            else:
                await asyncio.sleep(0.01)  # tiny sleep to reduce CPU

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        recorder.stop()
        recorder.delete()
        porcupine.delete()
        rhino.delete()
        await robot.close()
        print("Disconnected from robot")

if __name__ == "__main__":
    asyncio.run(main())