import RPi.GPIO as GPIO
import time

PIN = 4  # Change to your pin

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

def read_dht22():
    data = []
    GPIO.setup(PIN, GPIO.OUT)
    GPIO.output(PIN, GPIO.HIGH)
    time.sleep(0.05)
    GPIO.output(PIN, GPIO.LOW)
    time.sleep(0.02)
    GPIO.setup(PIN, GPIO.IN, GPIO.PUD_UP)

    # Collect signal transitions
    unchanged = 0
    last = -1
    while True:
        current = GPIO.input(PIN)
        data.append(current)
        if last != current:
            unchanged = 0
            last = current
        else:
            unchanged += 1
            if unchanged > 100:
                break

    # Parse bits
    bits = []
    state = 0
    length = 0
    pulls = []

    for i in data:
        length += 1
        if state == 0:
            if i == 0:
                state = 1
        elif state == 1:
            if i == 1:
                state = 2
        elif state == 2:
            if i == 0:
                pulls.append(length)
                length = 0

    if len(pulls) < 40:
        return None

    bits = []
    threshold = (min(pulls) + max(pulls)) / 2

    for l in pulls[:40]:
        bits.append(l > threshold)

    # Convert bits to 5 bytes
    bytes_out = []
    byte = 0
    for i,b in enumerate(bits):
        byte = (byte << 1) | (b == True)
        if (i+1) % 8 == 0:
            bytes_out.append(byte)
            byte = 0

    # Checksum
    if bytes_out[4] != ((bytes_out[0] + bytes_out[1] + bytes_out[2] + bytes_out[3]) & 255):
        return None

    humidity = (bytes_out[0] * 256 + bytes_out[1]) / 10
    temperature = (bytes_out[2] * 256 + bytes_out[3]) / 10
    return temperature, humidity


result = read_dht22()
GPIO.cleanup()

if result:
    temp, hum = result
    print(f"Temperature: {temp:.1f}°C")
    print(f"Humidity: {hum:.1f}%")
else:
    print("Failed to read sensor.")