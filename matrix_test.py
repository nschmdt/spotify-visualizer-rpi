#!/usr/bin/env python3
"""
RGB Matrix Hardware Test - Hello World!
Test script to verify your 32x32 RGB matrix is working correctly.
"""

import time
import sys
import math

# Try to import RGB matrix library
try:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions
    MATRIX_AVAILABLE = True
    print("✅ RGB Matrix library loaded successfully!")
except ImportError:
    print("❌ RGB Matrix library not found. Install with: pip3 install rpi-rgb-led-matrix")
    print("   Or visit: https://github.com/hzeller/rpi-rgb-led-matrix")
    MATRIX_AVAILABLE = False

def setup_matrix():
    """Initialize the RGB matrix with safe settings"""
    if not MATRIX_AVAILABLE:
        return None
        
    try:
        options = RGBMatrixOptions()
        options.rows = 32
        options.cols = 32
        options.chain_length = 1
        options.parallel = 1
        options.hardware_mapping = 'adafruit-hat-pwm'  # Common for Adafruit HATs
        options.gpio_slowdown = 2  # Start with 2, increase if you see flickering
        options.brightness = 30    # Start low for safety
        options.pwm_bits = 11
        options.pwm_lsb_nanoseconds = 130
        options.limit_refresh_rate_hz = 150
        
        matrix = RGBMatrix(options=options)
        print("✅ RGB Matrix initialized successfully!")
        print(f"   Size: {options.rows}x{options.cols}")
        print(f"   Brightness: {options.brightness}")
        print(f"   GPIO Slowdown: {options.gpio_slowdown}")
        return matrix
        
    except Exception as e:
        print(f"❌ Failed to initialize RGB matrix: {e}")
        print("\nTroubleshooting tips:")
        print("- Check GPIO connections")
        print("- Verify power supply (5V, 4A+)")
        print("- Try running with: sudo python3 matrix_test.py")
        print("- Check if another process is using the matrix")
        return None

def test_solid_colors(matrix):
    """Test basic colors"""
    print("\n🎨 Testing solid colors...")
    
    colors = [
        (255, 0, 0),    # Red
        (0, 255, 0),    # Green  
        (0, 0, 255),    # Blue
        (255, 255, 255), # White
        (0, 0, 0),      # Black (off)
    ]
    
    for r, g, b in colors:
        color_name = ["Red", "Green", "Blue", "White", "Black"][colors.index((r, g, b))]
        print(f"   Showing {color_name}...")
        
        for y in range(32):
            for x in range(32):
                matrix.SetPixel(x, y, r, g, b)
        
        time.sleep(1)

def test_rainbow(matrix):
    """Test rainbow effect"""
    print("\n🌈 Testing rainbow effect...")
    
    for frame in range(100):
        for y in range(32):
            for x in range(32):
                # Create rainbow effect
                hue = (x + y + frame) % 360
                r, g, b = hsv_to_rgb(hue, 1.0, 1.0)
                matrix.SetPixel(x, y, r, g, b)
        time.sleep(0.05)

def test_hello_world(matrix):
    """Display 'HELLO' text"""
    print("\n👋 Testing 'HELLO WORLD' text...")
    
    # Simple 5x7 font for 'HELLO'
    letters = {
        'H': [
            "█   █",
            "█   █", 
            "█████",
            "█   █",
            "█   █",
            "█   █",
            "█   █"
        ],
        'E': [
            "█████",
            "█    ",
            "█    ",
            "████ ",
            "█    ",
            "█    ",
            "█████"
        ],
        'L': [
            "█    ",
            "█    ",
            "█    ",
            "█    ",
            "█    ",
            "█    ",
            "█████"
        ],
        'O': [
            " ███ ",
            "█   █",
            "█   █",
            "█   █",
            "█   █",
            "█   █",
            " ███ "
        ]
    }
    
    # Clear matrix
    for y in range(32):
        for x in range(32):
            matrix.SetPixel(x, y, 0, 0, 0)
    
    # Draw HELLO
    text = "HELLO"
    start_x = 2
    start_y = 12
    
    for i, char in enumerate(text):
        if char in letters:
            letter_data = letters[char]
            for row, line in enumerate(letter_data):
                for col, pixel in enumerate(line):
                    if pixel == '█':
                        x = start_x + (i * 6) + col
                        y = start_y + row
                        if 0 <= x < 32 and 0 <= y < 32:
                            # Rainbow color for each letter
                            hue = i * 60
                            r, g, b = hsv_to_rgb(hue, 1.0, 1.0)
                            matrix.SetPixel(x, y, r, g, b)
    
    time.sleep(3)

def test_pixel_scan(matrix):
    """Test individual pixels"""
    print("\n🔍 Testing pixel scan...")
    
    # Clear matrix
    for y in range(32):
        for x in range(32):
            matrix.SetPixel(x, y, 0, 0, 0)
    
    # Scan through all pixels
    for y in range(32):
        for x in range(32):
            matrix.SetPixel(x, y, 255, 255, 255)  # White pixel
            time.sleep(0.01)
            matrix.SetPixel(x, y, 0, 0, 0)  # Turn off

def hsv_to_rgb(h, s, v):
    """Convert HSV to RGB"""
    h = h / 360.0
    c = v * s
    x = c * (1 - abs((h * 6) % 2 - 1))
    m = v - c
    
    if h < 1/6:
        r, g, b = c, x, 0
    elif h < 2/6:
        r, g, b = x, c, 0
    elif h < 3/6:
        r, g, b = 0, c, x
    elif h < 4/6:
        r, g, b = 0, x, c
    elif h < 5/6:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x
    
    return (int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))

def main():
    print("🚀 RGB Matrix Hardware Test")
    print("=" * 40)
    
    if not MATRIX_AVAILABLE:
        print("\n❌ Cannot run hardware tests without RGB matrix library.")
        print("Please install it first:")
        print("  pip3 install rpi-rgb-led-matrix")
        print("\nOr visit: https://github.com/hzeller/rpi-rgb-led-matrix")
        return
    
    # Initialize matrix
    matrix = setup_matrix()
    if not matrix:
        return
    
    print("\n🎯 Starting hardware tests...")
    print("Press Ctrl+C to stop at any time")
    
    try:
        # Run tests
        test_solid_colors(matrix)
        test_rainbow(matrix)
        test_hello_world(matrix)
        test_pixel_scan(matrix)
        
        print("\n✅ All tests completed successfully!")
        print("🎉 Your RGB matrix is working perfectly!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Tests stopped by user")
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
    finally:
        # Clear matrix before exit
        print("\n🧹 Clearing matrix...")
        for y in range(32):
            for x in range(32):
                matrix.SetPixel(x, y, 0, 0, 0)
        print("✅ Matrix cleared. Test complete!")

if __name__ == "__main__":
    main()
