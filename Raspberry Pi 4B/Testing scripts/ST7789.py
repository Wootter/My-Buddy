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
    time.sleep(0.120)
    
    write_cmd(0x36); write_data(0x00)  # MADCTL - screen orientation
    write_cmd(0x3A); write_data(0x55)  # COLMOD - 16bit color (RGB565)
    
    # Frame rate control
    write_cmd(0xB2); write_data(0x0C); write_data(0x0C); write_data(0x00); write_data(0x33); write_data(0x33)
    
    # Voltage settings  
    write_cmd(0xB7); write_data(0x35)  # Gate control
    write_cmd(0xBB); write_data(0x19)  # VCOM setting
    write_cmd(0xC0); write_data(0x2C)  # LCM control
    write_cmd(0xC2); write_data(0x01)  # VDV and VRH command enable
    write_cmd(0xC3); write_data(0x12)  # VRH set
    write_cmd(0xC4); write_data(0x20)  # VDV set
    write_cmd(0xC6); write_data(0x0F)  # Frame rate control
    write_cmd(0xD0); write_data(0xA4); write_data(0xA1)  # Power control
    
    # Gamma settings
    write_cmd(0xE0); write_data(0xD0); write_data(0x04); write_data(0x0D); write_data(0x11); write_data(0x13); write_data(0x2B); write_data(0x3F); write_data(0x54); write_data(0x4C); write_data(0x18); write_data(0x0D); write_data(0x0B); write_data(0x1F); write_data(0x23)
    write_cmd(0xE1); write_data(0xD0); write_data(0x04); write_data(0x0C); write_data(0x11); write_data(0x13); write_data(0x2C); write_data(0x3F); write_data(0x44); write_data(0x51); write_data(0x2F); write_data(0x1F); write_data(0x1F); write_data(0x20); write_data(0x23)
    
    write_cmd(0x21)   # inversion ON
    write_cmd(0x29)   # display ON
    time.sleep(0.100)


# ===== DRAWING FUNCTIONS =====
def set_window(x0,y0,x1,y1):
    write_cmd(0x2A); write_word(x0); write_word(x1)
    write_cmd(0x2B); write_word(y0); write_word(y1)
    write_cmd(0x2C)

def fill(color):
    set_window(0,0,239,239)
    high = color >> 8
    low  = color & 0xFF
    # Send in smaller chunks to avoid buffer overflow
    chunk_size = 2000  # Safe chunk size
    color_bytes = [high, low]
    total_pixels = 240 * 240
    
    for i in range(0, total_pixels * 2, chunk_size):
        remaining = min(chunk_size, (total_pixels * 2) - i)
        buf = color_bytes * (remaining // 2)
        spi.xfer2(buf)


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
