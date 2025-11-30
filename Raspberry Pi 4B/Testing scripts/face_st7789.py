import time
import board
import digitalio
from PIL import Image, ImageDraw
import adafruit_rgb_display.st7789 as st7789

# Pin config for Raspberry Pi
cs_pin = digitalio.DigitalInOut(board.D8)      # CS
dc_pin = digitalio.DigitalInOut(board.D25)     # DC
reset_pin = digitalio.DigitalInOut(board.D24)  # RST
spi = board.SPI()

disp = st7789.ST7789(
    spi,
    rotation=0,
    width=240,
    height=240,
    x_offset=0,
    y_offset=80,      # ← Most 1.54" 240x240 panels need this!
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=8000000
)

# Create white background
image = Image.new("RGB", (240, 240), (255, 255, 255))
draw = ImageDraw.Draw(image)

# Draw two black eyes (simple circles)
eye_radius = 20
eye_y = 90
eye_x1 = 70
eye_x2 = 170
draw.ellipse((eye_x1-eye_radius, eye_y-eye_radius, eye_x1+eye_radius, eye_y+eye_radius), fill=(0,0,0))
draw.ellipse((eye_x2-eye_radius, eye_y-eye_radius, eye_x2+eye_radius, eye_y+eye_radius), fill=(0,0,0))

# Display the face
print("Displaying face...")
disp.image(image)
time.sleep(5)
