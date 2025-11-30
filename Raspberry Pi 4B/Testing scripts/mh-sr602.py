import RPi.GPIO as GPIO
import time

PIN = 17 

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN, GPIO.IN)

try:
    while True:
        if GPIO.input(PIN):
            print("Motion detected!")
        else:
            print("No motion")

        time.sleep(0.2)

except KeyboardInterrupt:
    print("Exited")

finally:
    GPIO.cleanup()