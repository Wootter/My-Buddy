import smbus2
import time

ADDR = 0x10       
ALS_REG = 0x04    
BUS = 1           

GAIN = 0.2304     # multiplier from datasheet

bus = smbus2.SMBus(BUS)

# Configure sensor
bus.write_i2c_block_data(ADDR, 0x00, [0x00, 0x18])
time.sleep(0.05)

# Read raw value
raw = bus.read_word_data(ADDR, ALS_REG)

lux = round(raw * GAIN, 1)

bus.close()

print(f"Ambient Light: {lux} lux")