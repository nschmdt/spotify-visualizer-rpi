# Hardware Setup Guide

## 🛠️ Raspberry Pi Setup

### 1. Install Raspberry Pi OS
- Download [Raspberry Pi Imager](https://www.raspberrypi.org/downloads/)
- Flash Raspberry Pi OS Lite (64-bit) to SD card
- Enable SSH and set up WiFi during imaging process

### 2. Initial Pi Configuration
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y python3-pip python3-dev git

# Enable SPI and I2C (if needed)
sudo raspi-config
# Navigate to: Interfacing Options > SPI > Enable
# Navigate to: Interfacing Options > I2C > Enable
```

### 3. Install RGB Matrix Library
```bash
# Clone the RGB matrix library
git clone https://github.com/hzeller/rpi-rgb-led-matrix.git
cd rpi-rgb-led-matrix

# Install dependencies
sudo apt install -y python3-dev python3-pip libfreetype6-dev libjpeg-dev zlib1g-dev

# Build and install
make build-python
sudo make install-python

# Install Python bindings
sudo pip3 install rpi-rgb-led-matrix
```

## 🔌 RGB Matrix Hardware Setup

### Required Components
- **Raspberry Pi** (Zero 2 W recommended for performance)
- **32x32 RGB LED Matrix** (HUB75 interface)
- **RGB Matrix HAT** (Adafruit RGB Matrix HAT or similar)
- **Power Supply** (5V, 4A+ recommended)
- **Jumper wires** (if not using HAT)

### Wiring (HUB75 Interface)
```
Matrix Pin  →  Pi GPIO Pin
R1         →  GPIO 2  (Pin 3)
G1         →  GPIO 3  (Pin 5)  
B1         →  GPIO 4  (Pin 7)
R2         →  GPIO 17 (Pin 11)
G2         →  GPIO 27 (Pin 13)
B2         →  GPIO 22 (Pin 15)
A          →  GPIO 10 (Pin 19)
B          →  GPIO 9  (Pin 21)
C          →  GPIO 11 (Pin 23)
D          →  GPIO 5  (Pin 29)
CLK        →  GPIO 18 (Pin 12)
LAT        →  GPIO 23 (Pin 16)
OE         →  GPIO 24 (Pin 18)
```

### Power Requirements
- **Matrix**: 5V, 3-4A
- **Pi**: 5V, 2.5A
- **Total**: 5V, 6-7A power supply recommended

## 🧪 Testing Your Setup

### 1. Basic Hardware Test
```bash
# Run the hardware test
python3 matrix_test.py
```

This will test:
- ✅ Matrix initialization
- 🎨 Basic colors (Red, Green, Blue, White)
- 🌈 Rainbow effect
- 👋 "HELLO" text display
- 🔍 Pixel-by-pixel scan

### 2. Troubleshooting Common Issues

#### Matrix Not Lighting Up
- Check power supply (5V, 4A+)
- Verify all connections
- Try different `gpio_slowdown` values (1, 2, 3, 4)
- Check if another process is using GPIO

#### Flickering/Unstable Display
- Increase `gpio_slowdown` value
- Check power supply stability
- Verify all connections are secure
- Try different `pwm_lsb_nanoseconds` values

#### Permission Errors
```bash
# Run with sudo
sudo python3 matrix_test.py

# Or add user to gpio group
sudo usermod -a -G gpio pi
```

#### Import Errors
```bash
# Reinstall RGB matrix library
cd rpi-rgb-led-matrix
sudo make install-python
sudo pip3 install rpi-rgb-led-matrix
```

### 3. Matrix Configuration Tuning

Edit these values in your scripts for optimal performance:

```python
options = RGBMatrixOptions()
options.rows = 32
options.cols = 32
options.chain_length = 1
options.parallel = 1
options.hardware_mapping = 'adafruit-hat-pwm'  # or 'regular'
options.gpio_slowdown = 2  # Start with 2, increase if flickering
options.brightness = 50    # 0-100, start low
options.pwm_bits = 11
options.pwm_lsb_nanoseconds = 130
options.limit_refresh_rate_hz = 150
```

## 🎯 Next Steps

Once your hardware test passes:
1. ✅ Run `python3 matrix_test.py` - should show colors and "HELLO"
2. ✅ Install Spotify visualizer: `python3 setup.py`
3. ✅ Configure Spotify credentials
4. ✅ Run: `python3 spotify_visualizer.py`

## 📚 Additional Resources

- [RGB Matrix Library Documentation](https://github.com/hzeller/rpi-rgb-led-matrix)
- [Adafruit RGB Matrix HAT Guide](https://learn.adafruit.com/adafruit-rgb-matrix-bonnet-for-raspberry-pi)
- [Raspberry Pi GPIO Pinout](https://pinout.xyz/)

## 🔧 Advanced Configuration

### Multiple Matrices
```python
options.chain_length = 2  # For 2 matrices in chain
options.parallel = 2      # For 2 parallel chains
```

### Different Matrix Sizes
```python
options.rows = 16         # For 16x32 matrix
options.cols = 32
```

### Performance Tuning
```python
options.pwm_bits = 8      # Lower = faster, less color depth
options.pwm_lsb_nanoseconds = 100  # Adjust for your matrix
```
