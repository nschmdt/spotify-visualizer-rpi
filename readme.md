# Spotify LED Matrix Visualizer - Raspberry Pi Version

## Project Overview
A Python-based Spotify visualizer that displays album art on a 32x32 RGB LED matrix connected to a Raspberry Pi. Converts your currently playing Spotify track's album art into a beautiful LED display.

## Features
- ✅ **Spotify API Integration** - Real-time track monitoring with PKCE authentication
- ✅ **32x32 RGB Matrix Support** - Physical LED matrix display via rpi-rgb-led-matrix
- ✅ **Image Processing** - Automatic album art resizing and RGB extraction
- ✅ **Simulation Mode** - Test without hardware using ASCII art in terminal
- ✅ **Auto-startup** - Systemd service for automatic launch on boot
- ✅ **Error Handling** - Robust error handling and auto-restart capabilities

## Hardware Requirements
- Raspberry Pi (Zero 2 W recommended)
- 32x32 RGB LED Matrix (HUB75 interface)
- Adafruit RGB Matrix HAT or similar driver board
- Power supply (5V, 4A+ recommended)

## Quick Start

### 1. Setup Spotify App
1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Set redirect URI to: `http://localhost:8080/callback`
4. Copy your Client ID

### 2. Install Dependencies
```bash
# Run the setup script
python3 setup.py

# Or manually install
pip3 install -r requirements.txt
```

### 3. Configure
1. Update `CLIENT_ID` in `spotify_visualizer.py` with your Spotify app credentials
2. Adjust matrix settings in the script if needed

### 4. Run
```bash
python3 spotify_visualizer.py
```

## File Structure
```
spotify-visualizer-rpi/
├── spotify_visualizer.py      # Main application
├── callback_server.py         # OAuth callback handler
├── setup.py                   # Installation script
├── requirements.txt           # Python dependencies
├── spotify-visualizer.service # Systemd service file
├── readme.md                  # This file
└── index.html + script.js     # Original web version
```

## Configuration

### Matrix Settings
Edit these values in `spotify_visualizer.py`:
```python
MATRIX_SIZE = 32              # LED matrix size
REFRESH_INTERVAL = 1.0        # Update frequency (seconds)
options.brightness = 50       # Matrix brightness (0-100)
options.gpio_slowdown = 2     # GPIO timing (adjust if needed)
```

### Spotify Settings
```python
CLIENT_ID = 'your_client_id_here'
REDIRECT_URI = 'http://localhost:8080/callback'
SCOPE = 'user-read-currently-playing'
```

## Auto-Startup Setup

### Enable Systemd Service
```bash
# Copy service file
sudo cp spotify-visualizer.service /etc/systemd/system/

# Enable and start service
sudo systemctl enable spotify-visualizer
sudo systemctl start spotify-visualizer

# Check status
sudo systemctl status spotify-visualizer
```

### View Logs
```bash
# View recent logs
journalctl -u spotify-visualizer -f

# View all logs
journalctl -u spotify-visualizer
```

## Troubleshooting

### Matrix Not Displaying
- Check GPIO connections
- Verify power supply (5V, 4A+)
- Adjust `gpio_slowdown` value
- Check matrix configuration in code

### Authentication Issues
- Verify Client ID is correct
- Check redirect URI matches exactly
- Clear saved tokens: `rm .tokens .code_verifier`

### Permission Errors
- Run with `sudo` if needed for GPIO access
- Check file permissions: `chmod +x *.py`

## Development

### Testing Without Hardware
The script automatically detects if RGB matrix library is available. Without it, it runs in simulation mode showing ASCII art in the terminal.

### Adding Features
- Modify `checkCurrentTrack()` for additional track data
- Update `display_image_on_matrix()` for different display effects
- Add new image processing effects in `download_and_process_image()`

## Original Web Version
The `index.html` and `script.js` files contain the original web-based implementation for reference and testing.