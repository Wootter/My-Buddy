#!/usr/bin/env python3
"""
Face expressions for ST7789 1.54" Display
Supports: happy, angry, sad faces
"""

from PIL import Image, ImageDraw
import board
import busio
import digitalio
from adafruit_rgb_display import st7789

_display = None

def init_display():
    """Initialize the ST7789 display"""
    global _display
    
    if _display is not None:
        return _display
    
    # Create SPI bus
    spi = busio.SPI(clock=board.SCK, MOSI=board.MOSI)
    
    # Create digital pins for control signals
    cs_pin = digitalio.DigitalInOut(board.CE0)   # GPIO 8 (CE0)
    dc_pin = digitalio.DigitalInOut(board.D25)   # GPIO 25
    rst_pin = digitalio.DigitalInOut(board.D24)  # GPIO 24
    
    # Create display
    _display = st7789.ST7789(
        spi,
        cs=cs_pin,
        dc=dc_pin,
        rst=rst_pin,
        height=240,
        width=240,
        rotation=0,
        y_offset=80,
        x_offset=0,
        baudrate=40000000
    )
    
    return _display


def draw_happy_face():
    """Draw a happy face"""
    img = Image.new('RGB', (240, 240), color='white')
    draw = ImageDraw.Draw(img)
    
    # Eyes
    left_eye_x = 80
    right_eye_x = 160
    eye_y = 100
    eye_width = 35
    eye_height = 45
    
    # Draw left eye
    draw.ellipse(
        [left_eye_x - eye_width//2, eye_y - eye_height//2,
         left_eye_x + eye_width//2, eye_y + eye_height//2],
        fill='black'
    )
    
    # Draw right eye
    draw.ellipse(
        [right_eye_x - eye_width//2, eye_y - eye_height//2,
         right_eye_x + eye_width//2, eye_y + eye_height//2],
        fill='black'
    )
    
    # Smile (curved line)
    # Draw a smile using arc
    mouth_x1 = 70
    mouth_y1 = 150
    mouth_x2 = 170
    mouth_y2 = 190
    
    draw.arc([mouth_x1, mouth_y1, mouth_x2, mouth_y2], 0, 180, fill='black', width=3)
    
    return img


def draw_angry_face():
    """Draw an angry face"""
    img = Image.new('RGB', (240, 240), color='white')
    draw = ImageDraw.Draw(img)
    
    # Eyes
    left_eye_x = 80
    right_eye_x = 160
    eye_y = 100
    eye_width = 35
    eye_height = 45
    
    # Draw left eye
    draw.ellipse(
        [left_eye_x - eye_width//2, eye_y - eye_height//2,
         left_eye_x + eye_width//2, eye_y + eye_height//2],
        fill='black'
    )
    
    # Draw right eye
    draw.ellipse(
        [right_eye_x - eye_width//2, eye_y - eye_height//2,
         right_eye_x + eye_width//2, eye_y + eye_height//2],
        fill='black'
    )
    
    # Angry eyebrows (angled lines)
    # Left eyebrow (angled down-right)
    draw.line([60, 75, 100, 85], fill='black', width=3)
    
    # Right eyebrow (angled down-left)
    draw.line([140, 85, 180, 75], fill='black', width=3)
    
    # Frown (inverted arc)
    mouth_x1 = 70
    mouth_y1 = 155
    mouth_x2 = 170
    mouth_y2 = 195
    
    draw.arc([mouth_x1, mouth_y1, mouth_x2, mouth_y2], 180, 360, fill='black', width=3)
    
    return img


def draw_sad_face():
    """Draw a sad face"""
    img = Image.new('RGB', (240, 240), color='white')
    draw = ImageDraw.Draw(img)
    
    # Eyes
    left_eye_x = 80
    right_eye_x = 160
    eye_y = 100
    eye_width = 35
    eye_height = 45
    
    # Draw left eye
    draw.ellipse(
        [left_eye_x - eye_width//2, eye_y - eye_height//2,
         left_eye_x + eye_width//2, eye_y + eye_height//2],
        fill='black'
    )
    
    # Draw right eye
    draw.ellipse(
        [right_eye_x - eye_width//2, eye_y - eye_height//2,
         right_eye_x + eye_width//2, eye_y + eye_height//2],
        fill='black'
    )
    
    # Sad eyebrows (droopy angled lines)
    # Left eyebrow (angled down-left)
    draw.line([60, 85, 100, 75], fill='black', width=3)
    
    # Right eyebrow (angled down-right)
    draw.line([140, 75, 180, 85], fill='black', width=3)
    
    # Sad mouth (inverted arc, lower)
    mouth_x1 = 70
    mouth_y1 = 170
    mouth_x2 = 170
    mouth_y2 = 210
    
    draw.arc([mouth_x1, mouth_y1, mouth_x2, mouth_y2], 180, 360, fill='black', width=3)
    
    return img


def change_face(expression):
    """
    Change the face expression
    
    Args:
        expression (str): 'happy', 'angry', or 'sad'
    
    Returns:
        bool: True if successful, False if invalid expression
    """
    try:
        display = init_display()
        
        expression = expression.lower().strip()
        
        if expression == 'happy':
            img = draw_happy_face()
        elif expression == 'angry':
            img = draw_angry_face()
        elif expression == 'sad':
            img = draw_sad_face()
        else:
            print(f"Unknown expression: {expression}")
            return False
        
        display.image(img)
        print(f"Face changed to: {expression}")
        return True
        
    except Exception as e:
        print(f"Error changing face: {e}")
        return False