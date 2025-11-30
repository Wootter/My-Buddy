import time
import board
import adafruit_dht

# GPIO17 is physical pin 11 on Raspberry Pi
dht_sensor = adafruit_dht.DHT22(board.D17)

while True:
    try:
        temperature = dht_sensor.temperature
        humidity = dht_sensor.humidity
        print(f"Temp: {temperature:.1f}°C  Humidity: {humidity:.1f}%")
    except RuntimeError as e:
        # DHT sensors are a bit finicky, so retry on failure
        print("Reading error, retrying...")
    time.sleep(2)
