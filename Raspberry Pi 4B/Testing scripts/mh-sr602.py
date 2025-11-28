import RPi.GPIO as GPIO
import time

PIN = 17  # <-- change to your PIR sensor pin

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN, GPIO.IN)

print("MH-SR602 PIR Motion Sensor Test (Ctrl+C to quit)")

try:
    while True:
        if GPIO.input(PIN):
            print("Motion detected!")
        else:
            print("No motion")

        time.sleep(0.2)

except KeyboardInterrupt:
    print("Exiting...")

finally:
    GPIO.cleanup()