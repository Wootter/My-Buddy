import time
import asyncio
from tts_piper import speak
from changeFace import change_face
from viam.robot.client import RobotClient
from viam.components.sensor import Sensor as ViamSensor
from pvrecorder import PvRecorder
import pvporcupine
import pvrhino
import RPi.GPIO as GPIO

# CONFIG
ROBOT_ADDRESS = "my-buddy-main.1zxw399cc5.viam.cloud"
API_KEY_ID = "1dd258cc-c05f-4c45-b81a-97731e419e2d"
API_KEY = "nole6vqgb2biwxn535oj1x38et903ihp"

ACCESS_KEY = "cjmNT4hfxmJbe4vq5GRB6UAYw53HP9k7skrEAedIHmx1CllZn8W14Q=="
KEYWORD_PATH = "Hey-buddy_en_raspberry-pi_v4_0_0.ppn"
CONTEXT_PATH = "My-Buddy_en_raspberry-pi_v4_0_0.rhn"

ALERT_SOUND = "/usr/share/sounds/alsa/Front_Right.wav"
WAKEWORD_COOLDOWN = 300  # seconds

# LED CONFIG
LED_RED = 6
LED_GREEN = 5
LED_BLUE = 13
LED_PWM_FREQ = 1000  # 1 kHz

LED_RED_BRIGHTNESS = 1.0
LED_GREEN_BRIGHTNESS = 0.40
LED_BLUE_BRIGHTNESS = 1.0

# MIC
MIC_NAME_HINTS = [
    "PCM2902",        
    "USB",
    "Audio Codec",
]

# INTENT MAP
INTENT_SENSOR_MAP = {
    "showTemperature": {
        "sensor_name": "DHT22",
        "reading_key": "temperature_celsius",
        "unit": "°C",
    },
    "showHumidity": {
        "sensor_name": "DHT22",
        "reading_key": "humidity_percent",
        "unit": "%",
    },
    "showLightIntensity": {
        "sensor_name": "VEML7700",
        "reading_key": "lux",
        "unit": "lux",
    },
}

# VIAM SENSOR FETHCH
async def fetch_sensor_reading(robot, intent):
    cfg = INTENT_SENSOR_MAP.get(intent)
    if not cfg:
        return None, None

    try:
        sensor = ViamSensor.from_robot(robot, cfg["sensor_name"])
        readings = await sensor.get_readings()
        return readings.get(cfg["reading_key"]), cfg["unit"]
    except Exception as e:
        print(f"Error fetching {cfg['sensor_name']}: {e}")
        return None, cfg["unit"]


async def handle_sensor_intent(intent, slots, robot):
    room = slots.get("room", "inside")
    value, unit = await fetch_sensor_reading(robot, intent)

    text = (
        f"{intent} in {room}: {value} {unit}"
        if value is not None
        else f"No data for {intent} in {room}"
    )

    print(text)
    speak(text)


def handle_other_intent(intent, slots):
    if intent == "turnLight":
        text = f"Turning {slots.get('state')} light in {slots.get('room')}"
    elif intent == "setTimer":
        text = f"Setting timer for {slots.get('duration')}"
    else:
        text = f"Unknown intent: {intent}"

    print(text)
    speak(text)

def handle_change_face(slots):
    """Handle face change intent"""
    try:
        expression = slots.get('expression', '').lower().strip()
        
        if expression:
            success = change_face(expression)
            if success:
                text = f"Changing face to {expression}"
                print(text)
                speak(text)
        else:
            print("No expression specified")
    except Exception as e:
        print(f"Error changing face: {e}")

def set_led_color(r, g, b, pwm_red, pwm_green, pwm_blue):
    """Set LED to RGB color with brightness compensation"""
    pwm_red.ChangeDutyCycle((r / 255) * 100 * LED_RED_BRIGHTNESS)
    pwm_green.ChangeDutyCycle((g / 255) * 100 * LED_GREEN_BRIGHTNESS)
    pwm_blue.ChangeDutyCycle((b / 255) * 100 * LED_BLUE_BRIGHTNESS)


def handle_change_leds(slots, pwm_red, pwm_green, pwm_blue):
    """Handle LED color change intent"""
    try:
        shade = slots.get('shade', '').lower().strip()
        colour = slots.get('colour', '').lower().strip()
        
        # Combine shade and colour
        if shade:
            color_key = f"{shade} {colour}"
        else:
            color_key = colour
        
        # Color RGB values (light, normal, dark variants)
        colors = {
            'light red': (255, 127, 127),
            'red': (255, 0, 0),
            'dark red': (139, 0, 0),
            
            'light white': (255, 255, 255),
            'white': (255, 255, 255),
            'dark white': (200, 200, 200),
            
            'light pink': (255, 220, 230),
            'pink': (255, 192, 203),
            'dark pink': (219, 112, 147),
            
            'light purple': (200, 100, 255),
            'purple': (128, 0, 128),
            'dark purple': (75, 0, 130),
            
            'light orange': (255, 200, 124),
            'orange': (255, 165, 0),
            'dark orange': (255, 140, 0),
            
            'light yellow': (255, 255, 153),
            'yellow': (255, 255, 0),
            'dark yellow': (204, 204, 0),
            
            'light green': (144, 238, 144),
            'green': (0, 255, 0),
            'dark green': (0, 100, 0),
            
            'light blue': (173, 216, 230),
            'blue': (0, 0, 255),
            'dark blue': (0, 0, 139),
        }
        
        if color_key in colors:
            r, g, b = colors[color_key]
            set_led_color(r, g, b, pwm_red, pwm_green, pwm_blue)
            text = f"Changing LEDs to {color_key}"
            print(text)
            speak(text)
        else:
            print(f"Unknown color: {color_key}")
    except Exception as e:
        print(f"Error changing LEDs: {e}")


async def main():
    # ---- Setup LEDs ----
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LED_RED, GPIO.OUT)
    GPIO.setup(LED_GREEN, GPIO.OUT)
    GPIO.setup(LED_BLUE, GPIO.OUT)
    
    pwm_red = GPIO.PWM(LED_RED, LED_PWM_FREQ)
    pwm_green = GPIO.PWM(LED_GREEN, LED_PWM_FREQ)
    pwm_blue = GPIO.PWM(LED_BLUE, LED_PWM_FREQ)
    
    pwm_red.start(0)
    pwm_green.start(0)
    pwm_blue.start(0)
    
    # ---- Connect to Viam ----
    opts = RobotClient.Options.with_api_key(
        api_key=API_KEY,
        api_key_id=API_KEY_ID,
    )
    robot = await RobotClient.at_address(ROBOT_ADDRESS, opts)
    print("Connected to robot")

    # ---- Picovoice engines ----
    porcupine = pvporcupine.create(
        access_key=ACCESS_KEY,
        keyword_paths=[KEYWORD_PATH],
    )

    rhino = pvrhino.create(
        access_key=ACCESS_KEY,
        context_path=CONTEXT_PATH,
    )

    # ---- Select microphone ----
    devices = PvRecorder.get_available_devices()
    print("Available audio devices (PvRecorder):")
    for i, d in enumerate(devices):
        print(f"{i}: {d}")

    mic_index = None

    # Try known USB mic identifiers
    for i, d in enumerate(devices):
        if "monitor" in d.lower():
            continue
        if any(hint.lower() in d.lower() for hint in MIC_NAME_HINTS):
            mic_index = i
            break

    # Fallback
    if mic_index is None:
        for i, d in enumerate(devices):
            if "monitor" not in d.lower():
                mic_index = i
                break

    if mic_index is None:
        raise RuntimeError("No usable capture microphone found")

    print(f"Using microphone index {mic_index}: {devices[mic_index]}")

    recorder = PvRecorder(
        device_index=mic_index,
        frame_length=porcupine.frame_length,
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

            if not rhino.process(pcm):
                continue

            inference = rhino.get_inference()
            if not inference.intent:
                continue

            print("Intent:", inference.intent, "Slots:", inference.slots)
            conversation_expires_at = time.time() + WAKEWORD_COOLDOWN

            if inference.intent in INTENT_SENSOR_MAP:
                await handle_sensor_intent(inference.intent, inference.slots, robot)
            elif inference.intent == "changeLeds":
                handle_change_leds(inference.slots, pwm_red, pwm_green, pwm_blue)
            elif inference.intent == "changeFace":
                handle_change_face(inference.slots)
            else:
                handle_other_intent(inference.intent, inference.slots)

    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        pwm_red.stop()
        pwm_green.stop()
        pwm_blue.stop()
        GPIO.cleanup()
        recorder.stop()
        recorder.delete()
        porcupine.delete()
        rhino.delete()
        await robot.close()


if __name__ == "__main__":
    asyncio.run(main())