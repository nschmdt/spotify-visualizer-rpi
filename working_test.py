#!/usr/bin/env python3
import time
import sys

try:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions
    MATRIX_AVAILABLE = True
except ImportError:
    print("❌ RGB Matrix library not found")
    sys.exit(1)

def setup_matrix():
    try:
        options = RGBMatrixOptions()
        options.hardware_mapping = 'adafruit-hat'  # This is what worked!
        options.rows = 32
        options.cols = 32
        
        matrix = RGBMatrix(options=options)
        print("✅ RGB Matrix initialized successfully!")
        return matrix
    except Exception as e:
        print(f"❌ Failed to initialize RGB matrix: {e}")
        return None

def test_basic_colors(matrix):
    print("🎨 Testing basic colors...")
    
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 255)]
    
    for r, g, b in colors:
        print(f"   Showing color: R={r}, G={g}, B={b}")
        for y in range(32):
            for x in range(32):
                matrix.SetPixel(x, y, r, g, b)
        time.sleep(2)

def main():
    print("�� Working RGB Matrix Test")
    print("=" * 40)
    
    matrix = setup_matrix()
    if not matrix:
        return
    
    try:
        test_basic_colors(matrix)
        print("✅ Test completed successfully!")
    except KeyboardInterrupt:
        print("\n⏹️  Test stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        # Clear matrix
        for y in range(32):
            for x in range(32):
                matrix.SetPixel(x, y, 0, 0, 0)

if __name__ == "__main__":
    main()