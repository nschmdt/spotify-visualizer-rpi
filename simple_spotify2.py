#!/usr/bin/env python3
import time
import requests
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image
import io
import webbrowser
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sys
import os
import random
import math

# Configuration
CLIENT_ID = 'b245d267eebd4c97a090419d44fbd396'
REDIRECT_URI = 'http://127.0.0.1:8888/callback'
SCOPE = 'user-read-currently-playing'
MATRIX_SIZE = 32

def setup_matrix():
    options = RGBMatrixOptions()
    options.hardware_mapping = 'adafruit-hat'
    options.rows = 32
    options.cols = 32
    options.gpio_slowdown = 4  # Reduce flickering
    options.brightness = 100    # Much brighter! (was default ~50)
    options.pwm_bits = 8       # Better color depth
    options.pwm_lsb_nanoseconds = 200  # Smoother display
    return RGBMatrix(options=options)

# Global variables for callback handling
auth_code = None
auth_error = None

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code, auth_error
        
        # Parse the callback URL
        parsed_url = urlparse(self.path)
        params = parse_qs(parsed_url.query)
        
        if 'code' in params:
            auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
            <html>
                <head><title>Spotify Authorization</title></head>
                <body>
                    <h1>Authorization Successful!</h1>
                    <p>You can now close this tab and return to the terminal.</p>
                    <script>setTimeout(function(){ window.close(); }, 2000);</script>
                </body>
            </html>
            """)
        elif 'error' in params:
            auth_error = params['error'][0]
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
            <html>
                <head><title>Spotify Authorization Error</title></head>
                <body>
                    <h1>Authorization Failed</h1>
                    <p>Error: """ + auth_error.encode() + b"""</p>
                    <p>You can close this tab and try again.</p>
                </body>
            </html>
            """)
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"Invalid callback")
    
    def log_message(self, format, *args):
        # Suppress HTTP server logs
        pass

def start_callback_server():
    server = HTTPServer(('127.0.0.1', 8888), CallbackHandler)
    server.timeout = 1  # Short timeout for checking
    start_time = time.time()
    while auth_code is None and auth_error is None and (time.time() - start_time) < 30:
        server.handle_request()
    server.server_close()

def get_authorization_url():
    # Generate a simple code verifier
    import secrets
    import base64
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    
    # Generate code challenge
    import hashlib
    digest = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')
    
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPE,
        'code_challenge_method': 'S256',
        'code_challenge': code_challenge
    }
    
    from urllib.parse import urlencode
    auth_url = f"https://accounts.spotify.com/authorize?{urlencode(params)}"
    return auth_url, code_verifier

def soft_chaotic_transition(matrix, old_image, new_image, duration=7.0):
    """Gentle, organic pixel replacement with soft randomness and acceleration"""
    
    # Create a gentle wave pattern for pixel replacement
    wave_centers = [
        (8, 8), (24, 8), (8, 24), (24, 24), (16, 16)  # Multiple wave centers
    ]
    
    # Generate pixel positions with soft randomness
    positions = []
    for center_x, center_y in wave_centers:
        for radius in range(0, 20, 2):  # Gentle expansion
            for angle in range(0, 360, 15):  # Smooth rotation
                # Add soft randomness to position
                noise_x = random.uniform(-1, 1)
                noise_y = random.uniform(-1, 1)
                
                x = int(center_x + radius * math.cos(math.radians(angle)) + noise_x)
                y = int(center_y + radius * math.sin(math.radians(angle)) + noise_y)
                
                if 0 <= x < MATRIX_SIZE and 0 <= y < MATRIX_SIZE:
                    positions.append((x, y))
    
    # Shuffle for organic feel
    random.shuffle(positions)
    
    # Accelerating timing - starts slow, gets faster (5-10 seconds total)
    for i, (x, y) in enumerate(positions):
        # Calculate progress (0.0 to 1.0)
        progress = i / len(positions)
        
        # Acceleration curve - starts slow, accelerates
        # Use a quadratic curve for smooth acceleration
        acceleration_factor = progress * progress
        
        # Base delay starts high, gets lower as we progress
        # Adjusted for 5-10 second total duration
        base_delay = 0.05 * (1.0 - acceleration_factor * 0.7)  # 0.05s to 0.015s
        
        # Add some randomness
        delay = base_delay * random.uniform(0.8, 1.2)
        
        # Get new pixel color
        r, g, b = new_image.getpixel((x, y))
        
        # Apply soft color blending (gentle fade-in)
        alpha = min(1.0, i / (len(positions) * 0.3))  # Gentle fade-in
        old_r, old_g, old_b = old_image.getpixel((x, y))
        
        r = int(old_r * (1 - alpha) + r * alpha)
        g = int(old_g * (1 - alpha) + g * alpha)
        b = int(old_b * (1 - alpha) + b * alpha)
        
        # Fade up from black instead of binary on/off
        fade_steps = 8  # Number of fade steps
        for fade_step in range(fade_steps):
            fade_alpha = (fade_step + 1) / fade_steps
            fade_r = int(r * fade_alpha)
            fade_g = int(g * fade_alpha)
            fade_b = int(b * fade_alpha)
            
            matrix.SetPixel(x, y, fade_r, fade_g, fade_b)
            time.sleep(delay / fade_steps)

def display_image(matrix, image):
    """Display image on matrix with subtle color correction and fade-up"""
    for y in range(MATRIX_SIZE):
        for x in range(MATRIX_SIZE):
            r, g, b = image.getpixel((x, y))
            
            # Subtle color correction - much less aggressive
            r = int(r * 0.9)   # Slight red boost
            g = int(g * 1.0)   # Green unchanged
            b = int(b * 0.95)  # Slight blue reduction
            
            # Fade up from black instead of binary on/off
            fade_steps = 6  # Number of fade steps
            for fade_step in range(fade_steps):
                fade_alpha = (fade_step + 1) / fade_steps
                fade_r = int(r * fade_alpha)
                fade_g = int(g * fade_alpha)
                fade_b = int(b * fade_alpha)
                
                matrix.SetPixel(x, y, fade_r, fade_g, fade_b)
                time.sleep(0.01)  # Quick fade per pixel

def print_qr_code(url):
    """Print QR code to terminal"""
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=1,
            border=1,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        # Print QR code using ASCII characters
        qr.print_ascii(out=sys.stdout, tty=False, invert=True)
        return True
    except ImportError:
        print("⚠️  QR code module not installed. Install with: pip3 install qrcode[pil]")
        return False
    except Exception as e:
        print(f"⚠️  Could not generate QR code: {e}")
        return False

def main():
    print("🚀 Simple Spotify Visualizer")
    print("=" * 40)
    
    # Setup matrix
    matrix = setup_matrix()
    print("✅ RGB Matrix initialized")
    
    # Get authorization URL
    auth_url, code_verifier = get_authorization_url()
    
    print(f"\n🌐 Spotify Authorization Required")
    print("=" * 50)
    
    # Check if running over SSH and provide better instructions
    ssh_session = 'SSH_CLIENT' in os.environ or 'SSH_TTY' in os.environ
    if ssh_session:
        print("🔗 Detected SSH session!")
        print("   Option 1: SSH with port forwarding: ssh -L 8888:localhost:8888 pi@your-pi")
        print("   Option 2: Scan QR code with your phone and manually enter code")
        print("   Option 3: Copy URL to your local browser and manually enter code")
        print()
    
    # Start the callback server in a separate thread
    global auth_code, auth_error
    auth_code = None
    auth_error = None
    
    server_thread = threading.Thread(target=start_callback_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Show QR code for easy mobile access
    print("📱 Scan this QR code with your phone:")
    print()
    if print_qr_code(auth_url):
        print()
        print("📱 Or manually visit:")
    else:
        print("📋 Please visit this URL:")
    
    print(f"🔗 {auth_url}")
    print()
    
    # Try to open browser (works locally, not over SSH)
    if not ssh_session:
        try:
            webbrowser.open(auth_url)
            print("✅ Browser opened automatically")
        except Exception:
            pass
    
    print("⏱️  Waiting for automatic authorization (5 seconds)...")
    
    # Wait for the callback
    server_thread.join(timeout=5)
    
    if auth_error:
        print(f"❌ Authorization failed: {auth_error}")
        return
    
    if not auth_code:
        print("❌ Automatic authorization failed.")
        print("\n📋 Manual authorization:")
        print("1. Visit the URL above in your browser")
        print("2. Log into Spotify")
        print("3. You'll be redirected to a page that says 'can't connect'")
        print("4. Copy the 'code' parameter from the URL")
        print("5. Paste it here:")
        
        code = input("Enter the authorization code: ").strip()
        if not code:
            print("No code provided. Exiting.")
            return
        auth_code = code
    
    print("✅ Authorization code received!")
    
    # Exchange code for token
    data = {
        'client_id': CLIENT_ID,
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': REDIRECT_URI,
        'code_verifier': code_verifier
    }
    
    response = requests.post('https://accounts.spotify.com/api/token', data=data)
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data['access_token']
        print("✅ Successfully authenticated with Spotify!")
        
        # Start the visualizer loop
        print("🎵 Starting visualizer loop...")
        current_image = None
        current_track_id = None
        
        while True:
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get('https://api.spotify.com/v1/me/player/currently-playing', headers=headers)
            
            if response.status_code == 200:
                track_data = response.json()
                if track_data and track_data.get('item'):
                    track = track_data['item']
                    track_id = track.get('id')
                    album = track.get('album', {})
                    images = album.get('images', [])
                    
                    # Check if this is a new track
                    is_new_track = track_id != current_track_id
                    
                    if images:
                        image_url = images[0]['url']
                        print(f"🎵 Now playing: {track['name']} by {track['artists'][0]['name']}")
                        
                        # Download and process image
                        try:
                            img_response = requests.get(image_url, timeout=10)
                            if img_response.status_code == 200:
                                new_image = Image.open(io.BytesIO(img_response.content))
                                if new_image.mode != 'RGB':
                                    new_image = new_image.convert('RGB')
                                new_image = new_image.resize((MATRIX_SIZE, MATRIX_SIZE), Image.Resampling.LANCZOS)
                                
                                # Display with transition if new track
                                if current_image is None or not is_new_track:
                                    # First image or same track - direct display
                                    display_image(matrix, new_image)
                                else:
                                    # New track - soft chaotic transition
                                    print("🌊 Transitioning to new track...")
                                    soft_chaotic_transition(matrix, current_image, new_image, duration=7.0)
                                
                                current_image = new_image
                                current_track_id = track_id
                                
                        except Exception as e:
                            print(f"Error processing image: {e}")
                    else:
                        print("No album art available")
                else:
                    print("No track currently playing")
            else:
                print("No track currently playing")
            
            time.sleep(1)  # Check every 1 second
    else:
        print(f"❌ Authentication failed: {response.status_code} - {response.text}")

if __name__ == "__main__":
    main()