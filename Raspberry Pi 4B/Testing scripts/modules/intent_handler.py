"""Intent recognition and command handling module"""
import asyncio
import RPi.GPIO as GPIO
from tts_piper import speak
from changeFace import change_face
import pvrhino


# ---- INTENT SENSOR MAP ----
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

# ---- COLOR MAP ----
COLOR_MAP = {
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


def setup_rhino(access_key, context_path):
    """
    Initialize Rhino intent recognition engine
    
    Args:
        access_key: Picovoice access key
        context_path: Path to Rhino context model
        
    Returns:
        Initialized Rhino instance
    """
    rhino = pvrhino.create(
        access_key=access_key,
        context_path=context_path,
    )
    return rhino


async def handle_intent(intent, slots, robot, pwm_red, pwm_green, pwm_blue, led_brightness):
    """
    Main intent dispatcher - routes to appropriate handler
    
    Args:
        intent: Intent name from Rhino
        slots: Intent slots/parameters
        robot: Viam robot client
        pwm_red, pwm_green, pwm_blue: LED PWM objects
        led_brightness: LED brightness settings dict
    """
    if intent in INTENT_SENSOR_MAP:
        await _handle_sensor_intent(intent, slots, robot)
    elif intent == "changeLeds":
        _handle_change_leds(slots, pwm_red, pwm_green, pwm_blue, led_brightness)
    elif intent == "changeFace":
        _handle_change_face(slots)
    else:
        _handle_other_intent(intent, slots)


# ---- SENSOR HANDLERS ----
async def _handle_sensor_intent(intent, slots, robot):
    """Handle sensor reading intents"""
    from viam.components.sensor import Sensor as ViamSensor
    from viam.errors import ComponentNotFoundError
    
    cfg = INTENT_SENSOR_MAP.get(intent)
    room = slots.get("room", "inside")
    
    try:
        # Check if sensor exists
        try:
            sensor = ViamSensor.from_robot(robot, cfg["sensor_name"])
            readings = await sensor.get_readings()
            value = readings.get(cfg["reading_key"])
            
            if value is not None:
                text = f"{intent} in {room}: {value} {cfg['unit']}"
            else:
                text = f"No data for {intent} in {room}"
        except (ComponentNotFoundError, ValueError) as ve:
             # If specific sensor not found, try to list available resources to help debug
            resources = await robot.get_resource_names()
            sensor_names = [r.name for r in resources if r.subtype == 'sensor']
            text = f"Sensor '{cfg['sensor_name']}' not found. Available sensors: {', '.join(sensor_names)}"
            print(f"DEBUG: All resources: {[r.name for r in resources]}")

    except Exception as e:
        text = f"Error reading {cfg['sensor_name']}: {type(e).__name__}: {e}"
    
    print(text)
    speak(text)


# ---- LED HANDLER ----
def _set_led_color(r, g, b, pwm_red, pwm_green, pwm_blue, led_brightness):
    """Set LED to RGB color with brightness compensation"""
    pwm_red.ChangeDutyCycle((r / 255) * 100 * led_brightness['red'])
    pwm_green.ChangeDutyCycle((g / 255) * 100 * led_brightness['green'])
    pwm_blue.ChangeDutyCycle((b / 255) * 100 * led_brightness['blue'])


def _handle_change_leds(slots, pwm_red, pwm_green, pwm_blue, led_brightness):
    """Handle LED color change intent"""
    try:
        shade = slots.get('shade', '').lower().strip()
        colour = slots.get('colour', '').lower().strip()
        
        # Combine shade and colour
        if shade:
            color_key = f"{shade} {colour}"
        else:
            color_key = colour
        
        if color_key in COLOR_MAP:
            r, g, b = COLOR_MAP[color_key]
            _set_led_color(r, g, b, pwm_red, pwm_green, pwm_blue, led_brightness)
    except Exception as e:
        print(f"Error changing LEDs: {e}")


# ---- FACE HANDLER ----
def _handle_change_face(slots):
    """Handle face change intent"""
    try:
        expression = slots.get('expression', '').lower().strip()
        
        if expression:
            change_face(expression)
    except Exception as e:
        print(f"Error changing face: {e}")


# ---- OTHER INTENTS ----
def _handle_other_intent(intent, slots):
    """Handle other intents (timer, lights, etc.)"""
    if intent == "turnLight":
        text = f"Turning {slots.get('state')} light in {slots.get('room')}"
    elif intent == "setTimer":
        text = f"Setting timer for {slots.get('duration')}"
    else:
        text = f"Understood: {intent}"
    
    print(text)
    speak(text)


# ---- LED SETUP ----
def setup_leds(led_pins, led_pwm_freq):
    """
    Initialize GPIO LEDs
    
    Args:
        led_pins: Dict with 'red', 'green', 'blue' pins
        led_pwm_freq: PWM frequency in Hz
        
    Returns:
        Tuple of (pwm_red, pwm_green, pwm_blue)
    """
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(led_pins['red'], GPIO.OUT)
    GPIO.setup(led_pins['green'], GPIO.OUT)
    GPIO.setup(led_pins['blue'], GPIO.OUT)
    
    pwm_red = GPIO.PWM(led_pins['red'], led_pwm_freq)
    pwm_green = GPIO.PWM(led_pins['green'], led_pwm_freq)
    pwm_blue = GPIO.PWM(led_pins['blue'], led_pwm_freq)
    
    pwm_red.start(0)
    pwm_green.start(0)
    pwm_blue.start(0)
    
    return pwm_red, pwm_green, pwm_blue
