import RPi.GPIO as GPIO
import time

# GPIO pin assignments
RED = 6
GREEN = 5
BLUE = 13

GPIO.setmode(GPIO.BCM)

GPIO.setup(RED, GPIO.OUT)
GPIO.setup(GREEN, GPIO.OUT)
GPIO.setup(BLUE, GPIO.OUT)

# PWM at 1 kHz (stable for LED dimming)
red_pwm = GPIO.PWM(RED, 1000)
green_pwm = GPIO.PWM(GREEN, 1000)
blue_pwm = GPIO.PWM(BLUE, 1000)

# Brightness compensation factors (tune these to balance colors)
red_brightness = 1.0
green_brightness = 0.40  # Further reduced
blue_brightness = 1.0

# Start with LEDs off
red_pwm.start(0)
green_pwm.start(0)
blue_pwm.start(0)

try:
    # Get hex color input
    hex_color = int(input("Enter a hex color code (e.g., 0xFF5733): "), 16)
    
    # Extract RGB values from hex
    red = (hex_color >> 16) & 0xFF
    green = (hex_color >> 8) & 0xFF
    blue = hex_color & 0xFF
    
    # Set LED colors based on hex input with brightness compensation
    red_pwm.ChangeDutyCycle((red / 255) * 100 * red_brightness)
    green_pwm.ChangeDutyCycle((green / 255) * 100 * green_brightness)
    blue_pwm.ChangeDutyCycle((blue / 255) * 100 * blue_brightness)

    time.sleep(5)  # Keep the color for 5 seconds

finally:
    red_pwm.stop()
    green_pwm.stop()
    blue_pwm.stop()
    GPIO.cleanup()
