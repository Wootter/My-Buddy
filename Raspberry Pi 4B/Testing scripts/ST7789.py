#!/usr/bin/env python3
import time
import spidev
import RPi.GPIO as GPIO

# ==== GPIO SETUP (BCM MODE) ====
DC  = 25   # Data/Command
RST = 24   # Reset
BL  = 18   # Backlight (optional PWM)

# ==== SPI SETTINGS ====
SPI_BUS = 0
SPI_DEVICE = 0
SPI_SPEED = 8000000    # 8MHz - more stable for displays

# ==== COLOR DEFINITIONS (RGB565) ====
BLACK  = 0x0000
RED    = 0xF800
GREEN  = 0x07E0
BLUE   = 0x001F
WHITE  = 0xFFFF
COLORS = [RED, GREEN, BLUE, WHITE]


# ===== LOW LEVEL PIN_WRITE =====
def write_cmd(value):
    GPIO.output(DC, GPIO.LOW)
    spi.xfer2([value])

def write_data(value):
    GPIO.output(DC, GPIO.HIGH)
    spi.xfer2([value])

def write_word(value):
    GPIO.output(DC, GPIO.HIGH)
    spi.xfer2([value >> 8, value & 0xFF])


# ===== INITIALISATION SEQUENCE =====
def init_display():
    write_cmd(0x01)   # software reset
    time.sleep(0.150)
    write_cmd(0x11)   # sleep out
    time.sleep(0.500)
    write_cmd(0x3A); write_data(0x55)  # 16bit color RGB565
    write_cmd(0x36); write_data(0x00)  # MADCTL normal orientation
    write_cmd(0x29)   # display ON
    time.sleep(0.100)


# ===== DRAWING FUNCTIONS =====

def fill(color):
    write_cmd(0x2A)  # Column address
    write_data(0x00); write_data(0x00)  # Start column 0
    write_data(0x00); write_data(0xEF)  # End column 239
    
    write_cmd(0x2B)  # Row address  
    write_data(0x00); write_data(0x00)  # Start row 0
    write_data(0x00); write_data(0xEF)  # End row 239
    
    write_cmd(0x2C)  # Memory write
    
    # Send color data - just blast it all at once, smaller chunks
    high = color >> 8
    low = color & 0xFF
    
    for _ in range(240):  # 240 rows
        chunk = [high, low] * 240  # 240 pixels per row
        spi.xfer2(chunk)


# ===== MAIN TEST =====
GPIO.setmode(GPIO.BCM)
GPIO.setup(DC, GPIO.OUT)
GPIO.setup(RST, GPIO.OUT)
GPIO.setup(BL, GPIO.OUT)

GPIO.output(BL, 1)   # Turn on backlight

GPIO.output(RST, 0); time.sleep(0.05)
GPIO.output(RST, 1); time.sleep(0.05)

spi = spidev.SpiDev()
spi.open(SPI_BUS, SPI_DEVICE)
spi.max_speed_hz = SPI_SPEED
spi.mode = 0

print("Initializing ST7789...")
init_display()

print("Filling colors...")
for i,c in enumerate(COLORS):
    print(f"Showing color {i+1}/4")
    fill(c)
    time.sleep(1)

print("Done!")
spi.close()
GPIO.cleanup()
