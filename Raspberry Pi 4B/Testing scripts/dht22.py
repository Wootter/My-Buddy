import RPi.GPIO as GPIO
import time

PIN = 4  # Change to your pin

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

def read_dht22():
    data = []
    print(f"DEBUG: Using GPIO pin {PIN}")
    
    GPIO.setup(PIN, GPIO.OUT)
    GPIO.output(PIN, GPIO.HIGH)
    time.sleep(0.05)
    GPIO.output(PIN, GPIO.LOW)
    time.sleep(0.02)
    GPIO.setup(PIN, GPIO.IN, GPIO.PUD_UP)
    print("DEBUG: Sent start signal, waiting for response...")

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

    print(f"DEBUG: Collected {len(data)} data points")

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

    print(f"DEBUG: Found {len(pulls)} signal pulses (need 40)")
    if len(pulls) > 0:
        print(f"DEBUG: Pulse lengths - min: {min(pulls)}, max: {max(pulls)}")

    if len(pulls) < 40:
        print(f"DEBUG: Not enough pulses - got {len(pulls)}, need 40")
        return None

    bits = []
    threshold = (min(pulls) + max(pulls)) / 2
    print(f"DEBUG: Using threshold: {threshold}")

    for l in pulls[:40]:
        bits.append(l > threshold)

    print(f"DEBUG: Converted to bits: {''.join(['1' if b else '0' for b in bits])}")

    # Convert bits to 5 bytes
    bytes_out = []
    byte = 0
    for i,b in enumerate(bits):
        byte = (byte << 1) | (b == True)
        if (i+1) % 8 == 0:
            bytes_out.append(byte)
            byte = 0

    print(f"DEBUG: Raw bytes: {[hex(b) for b in bytes_out]}")

    # Checksum
    calculated_checksum = (bytes_out[0] + bytes_out[1] + bytes_out[2] + bytes_out[3]) & 255
    received_checksum = bytes_out[4]
    print(f"DEBUG: Checksum - calculated: {hex(calculated_checksum)}, received: {hex(received_checksum)}")
    
    if received_checksum != calculated_checksum:
        print("DEBUG: Checksum mismatch!")
        return None

    humidity = (bytes_out[0] * 256 + bytes_out[1]) / 10
    temperature = (bytes_out[2] * 256 + bytes_out[3]) / 10
    print(f"DEBUG: Parsed - Temperature: {temperature}°C, Humidity: {humidity}%")
    return temperature, humidity


result = read_dht22()
GPIO.cleanup()

if result:
    temp, hum = result
    print(f"Temperature: {temp:.1f}°C")
    print(f"Humidity: {hum:.1f}%")
else:
    print("Failed to read sensor.")