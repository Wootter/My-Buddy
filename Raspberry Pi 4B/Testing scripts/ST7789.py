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
SPI_SPEED = 16000000   # 16MHz max stable

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
    write_cmd(0x3A); write_data(0x55)  # 16bit color
    write_cmd(0x36); write_data(0x00)  # MADCTL screen orientation
    write_cmd(0x21)   # inversion ON
    time.sleep(0.010)
    write_cmd(0x29)   # display ON
    time.sleep(0.500)


# ===== DRAWING FUNCTIONS =====
def set_window(x0,y0,x1,y1):
    write_cmd(0x2A); write_word(x0); write_word(x1)
    write_cmd(0x2B); write_word(y0); write_word(y1)
    write_cmd(0x2C)

def fill(color):
    set_window(0,0,239,239)
    high = color >> 8
    low  = color & 0xFF
    buf = [high, low] * (240*240//2)   # safe buffer size
    for _ in range(2): spi.xfer2(buf)


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
