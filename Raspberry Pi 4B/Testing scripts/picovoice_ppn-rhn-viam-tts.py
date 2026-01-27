import time
import asyncio
from tts_piper import speak
from viam.robot.client import RobotClient
from viam.components.sensor import Sensor as ViamSensor
from pvrecorder import PvRecorder
import pvporcupine
import pvrhino

# ------------------------
# CONFIG
# ------------------------
ROBOT_ADDRESS = "my-buddy-main.1zxw399cc5.viam.cloud"
API_KEY_ID = "1dd258cc-c05f-4c45-b81a-97731e419e2d"
API_KEY = "nole6vqgb2biwxn535oj1x38et903ihp"

ACCESS_KEY = 'cjmNT4hfxmJbe4vq5GRB6UAYw53HP9k7skrEAedIHmx1CllZn8W14Q=='
KEYWORD_PATH = 'Hey-buddy_en_raspberry-pi_v4_0_0.ppn'
CONTEXT_PATH = 'My-Buddy_en_raspberry-pi_v4_0_0.rhn'
USB_MIC_INDEX = 2
RESPEAKER_DEVICE = 'plughw:3,0'
ALERT_SOUND = '/usr/share/sounds/alsa/Front_Right.wav'
WAKEWORD_COOLDOWN = 300  # 5 minutes

# Map intents to Viam sensors and reading keys
INTENT_SENSOR_MAP = {
    "showTemperature": {"sensor_name": "DHT22", "reading_key": "temperature_celsius", "unit": "°C"},
    "showHumidity": {"sensor_name": "DHT22", "reading_key": "humidity_percent", "unit": "%"},
    "showLightIntensity": {"sensor_name": "VEML7700", "reading_key": "lux", "unit": "lux"},
}

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
        text = f"{intent} in {room}: {value} {unit}"
    else:
        text = f"No data for {intent} in {room}"
    print(text)
    speak(text)

# ------------------------
# OTHER INTENT HANDLER
# ------------------------
def handle_other_intent(intent, slots):
    if intent == "turnLight":
        text = f"Turning {slots.get('state')} light in {slots.get('room')}"
    elif intent == "setTimer":
        text = f"Setting timer for {slots.get('duration')}"
    else:
        text = f"Unknown intent: {intent}"
    print(text)
    speak(text)

# ------------------------
# MAIN LOOP
# ------------------------
async def main():
    opts = RobotClient.Options.with_api_key(
        api_key=API_KEY,
        api_key_id=API_KEY_ID
    )
    robot = await RobotClient.at_address(ROBOT_ADDRESS, opts)
    print("Connected to robot")

    porcupine = pvporcupine.create(
        access_key=ACCESS_KEY,
        keyword_paths=[KEYWORD_PATH]
    )
    rhino = pvrhino.create(
        access_key=ACCESS_KEY,
        context_path=CONTEXT_PATH
    )

    recorder = PvRecorder(
        device_index=USB_MIC_INDEX,
        frame_length=porcupine.frame_length
    )
    recorder.start()

    conversation_active = False
    conversation_expires_at = 0

    print("Listening for wake word...")

    try:
        while True:
            pcm = recorder.read()
            now = time.time()

            # ---- SLEEP MODE ----
            if not conversation_active:
                if porcupine.process(pcm) >= 0:
                    conversation_active = True
                    conversation_expires_at = now + WAKEWORD_COOLDOWN
                    print("Wake word detected")
                    speak("Yes?")
                continue

            # ---- ACTIVE MODE ----
            if now > conversation_expires_at:
                conversation_active = False
                print("Conversation expired")
                continue

            is_finalized = rhino.process(pcm)
            if not is_finalized:
                continue

            inference = rhino.get_inference()
            intent = inference.intent
            slots = inference.slots

            if not intent:
                continue

            print("Intent:", intent, "Slots:", slots)
            conversation_expires_at = time.time() + WAKEWORD_COOLDOWN

            if intent in INTENT_SENSOR_MAP:
                await handle_sensor_intent(intent, slots, robot)
            else:
                handle_other_intent(intent, slots)

    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        recorder.stop()
        recorder.delete()
        porcupine.delete()
        rhino.delete()
        await robot.close()


if __name__ == "__main__":
    asyncio.run(main())