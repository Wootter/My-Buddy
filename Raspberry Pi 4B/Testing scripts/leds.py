import RPi.GPIO as GPIO
import time

# GPIO pin assignments
RED = 5
GREEN = 6
BLUE = 12

GPIO.setmode(GPIO.BCM)

GPIO.setup(RED, GPIO.OUT)
GPIO.setup(GREEN, GPIO.OUT)
GPIO.setup(BLUE, GPIO.OUT)

# PWM at 1 kHz (stable for LED dimming)
red_pwm = GPIO.PWM(RED, 1000)
green_pwm = GPIO.PWM(GREEN, 1000)
blue_pwm = GPIO.PWM(BLUE, 1000)

# Start with LEDs off
red_pwm.start(0)
green_pwm.start(0)
blue_pwm.start(0)

try:
    # ---- Quick test sequence ----

    # Red
    red_pwm.ChangeDutyCycle(100)
    time.sleep(1)
    red_pwm.ChangeDutyCycle(0)

    # Green
    green_pwm.ChangeDutyCycle(100)
    time.sleep(1)
    green_pwm.ChangeDutyCycle(0)

    # Blue
    blue_pwm.ChangeDutyCycle(100)
    time.sleep(1)
    blue_pwm.ChangeDutyCycle(0)

    # White (mix all)
    red_pwm.ChangeDutyCycle(100)
    green_pwm.ChangeDutyCycle(100)
    blue_pwm.ChangeDutyCycle(100)
    time.sleep(1)

    # Fade demo
    for dc in range(0, 101):
        red_pwm.ChangeDutyCycle(dc)
        green_pwm.ChangeDutyCycle(100 - dc)
        blue_pwm.ChangeDutyCycle(dc // 2)
        time.sleep(0.02)

finally:
    red_pwm.stop()
    green_pwm.stop()
    blue_pwm.stop()
    GPIO.cleanup()
