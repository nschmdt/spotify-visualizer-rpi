#!/usr/bin/env python3
"""
Spotify LED Matrix Visualizer for Raspberry Pi
Converts album art to 32x32 RGB LED matrix display
"""

import os
import sys
import time
import base64
import hashlib
import secrets
import webbrowser
from urllib.parse import urlencode, parse_qs, urlparse
import requests
from PIL import Image
import io

# RGB Matrix imports (will be installed on Pi)
try:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions
    MATRIX_AVAILABLE = True
except ImportError:
    print("RGB Matrix library not available - running in simulation mode")
    MATRIX_AVAILABLE = False

# Configuration
CLIENT_ID = 'b245d267eebd4c97a090419d44fbd396'  # Same as your JS version
REDIRECT_URI = 'http://localhost:8080/callback'
SCOPE = 'user-read-currently-playing'
MATRIX_SIZE = 32
REFRESH_INTERVAL = 1.0  # seconds

class SpotifyVisualizer:
    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.matrix = None
        self.setup_matrix()
        
    def setup_matrix(self):
    """Initialize the RGB matrix hardware"""
    if not MATRIX_AVAILABLE:
        print("Running in simulation mode - no physical matrix")
        return None
        
    try:
        options = RGBMatrixOptions()
        options.rows = MATRIX_SIZE
        options.cols = MATRIX_SIZE
        options.chain_length = 1
        options.parallel = 1
        options.hardware_mapping = 'adafruit-hat'  # Use the working mapping!
        options.gpio_slowdown = 4
        options.brightness = 20
        
        self.matrix = RGBMatrix(options=options)
        print("RGB Matrix initialized successfully")
    except Exception as e:
        print(f"Failed to initialize RGB matrix: {e}")
        self.matrix = None

    def generate_code_verifier(self, length=64):
        """Generate PKCE code verifier"""
        return base64.urlsafe_b64encode(secrets.token_bytes(length)).decode('utf-8').rstrip('=')

    def generate_code_challenge(self, code_verifier):
        """Generate PKCE code challenge"""
        digest = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        return base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')

    def get_authorization_url(self):
        """Generate Spotify authorization URL with PKCE"""
        code_verifier = self.generate_code_verifier()
        code_challenge = self.generate_code_challenge(code_verifier)
        
        # Store code verifier for later use
        with open('.code_verifier', 'w') as f:
            f.write(code_verifier)
        
        params = {
            'client_id': CLIENT_ID,
            'response_type': 'code',
            'redirect_uri': REDIRECT_URI,
            'scope': SCOPE,
            'code_challenge_method': 'S256',
            'code_challenge': code_challenge
        }
        
        auth_url = f"https://accounts.spotify.com/authorize?{urlencode(params)}"
        return auth_url

    def start_callback_server(self):
        """Start a simple HTTP server to handle OAuth callback"""
        import threading
        import http.server
        import socketserver
        
        class CallbackHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path.startswith('/callback'):
                    parsed_url = urlparse(self.path)
                    query_params = parse_qs(parsed_url.query)
                    
                    if 'code' in query_params:
                        code = query_params['code'][0]
                        print(f"\n✅ Authorization code received: {code}")
                        
                        # Save code to file
                        with open('.auth_code', 'w') as f:
                            f.write(code)
                        
                        # Send response to browser
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                        self.wfile.write(b'''
                        <html><body style="font-family: Arial; text-align: center; padding: 50px; background: #1DB954; color: white;">
                        <h1>Authorization Complete!</h1>
                        <p>You can close this window and return to the terminal.</p>
                        </body></html>
                        ''')
                    else:
                        print(f"\n❌ No authorization code found")
                        self.send_response(400)
                        self.end_headers()
                else:
                    self.send_response(404)
                    self.end_headers()
        
        try:
            with socketserver.TCPServer(("", 8080), CallbackHandler) as httpd:
                print("🌐 Callback server started on http://localhost:8080")
                print("Waiting for authorization...")
                httpd.timeout = 1  # Allow for keyboard interrupt
                while True:
                    httpd.handle_request()
                    if os.path.exists('.auth_code'):
                        break
        except OSError as e:
            if e.errno == 48:  # Address already in use
                print("⚠️  Port 8080 is in use. Please close other applications and try again.")
            else:
                print(f"❌ Failed to start callback server: {e}")
            return False
        return True

    def exchange_code_for_token(self, code):
        """Exchange authorization code for access token"""
        try:
            with open('.code_verifier', 'r') as f:
                code_verifier = f.read().strip()
        except FileNotFoundError:
            print("Code verifier not found. Please restart authentication.")
            return False
            
        data = {
            'client_id': CLIENT_ID,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URI,
            'code_verifier': code_verifier
        }
        
        response = requests.post('https://accounts.spotify.com/api/token', data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data['access_token']
            self.refresh_token = token_data.get('refresh_token')
            
            # Save tokens for future use
            with open('.tokens', 'w') as f:
                f.write(f"{self.access_token}\n{self.refresh_token or ''}")
            
            print("Successfully authenticated with Spotify!")
            return True
        else:
            print(f"Token exchange failed: {response.status_code} - {response.text}")
            return False

    def load_saved_tokens(self):
        """Load previously saved tokens"""
        try:
            with open('.tokens', 'r') as f:
                lines = f.read().strip().split('\n')
                if len(lines) >= 1:
                    self.access_token = lines[0]
                    if len(lines) >= 2:
                        self.refresh_token = lines[1]
                    return True
        except FileNotFoundError:
            pass
        return False

    def get_current_track(self):
        """Get currently playing track from Spotify API"""
        if not self.access_token:
            return None
            
        headers = {'Authorization': f'Bearer {self.access_token}'}
        response = requests.get('https://api.spotify.com/v1/me/player/currently-playing', headers=headers)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            print("Token expired, need to re-authenticate")
            return None
        else:
            return None

    def download_and_process_image(self, image_url):
        """Download album art and process it for the LED matrix"""
        try:
            response = requests.get(image_url, timeout=10)
            if response.status_code == 200:
                # Open image with PIL
                image = Image.open(io.BytesIO(response.content))
                
                # Convert to RGB if needed
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Resize to matrix size
                image = image.resize((MATRIX_SIZE, MATRIX_SIZE), Image.Resampling.LANCZOS)
                
                return image
        except Exception as e:
            print(f"Error processing image: {e}")
        
        return None

    def display_image_on_matrix(self, image):
        """Display the processed image on the RGB matrix"""
        if not self.matrix:
            # Simulation mode - print to console
            self.simulate_matrix_display(image)
            return
            
        try:
            # Convert PIL image to RGB matrix format
            for y in range(MATRIX_SIZE):
                for x in range(MATRIX_SIZE):
                    r, g, b = image.getpixel((x, y))
                    self.matrix.SetPixel(x, y, r, g, b)
        except Exception as e:
            print(f"Error displaying on matrix: {e}")

    def simulate_matrix_display(self, image):
        """Simulate matrix display in console (for testing without hardware)"""
        print("\n" + "="*50)
        print("LED MATRIX SIMULATION (32x32)")
        print("="*50)
        
        # Create a simple ASCII representation
        for y in range(0, MATRIX_SIZE, 2):  # Skip every other row for readability
            row = ""
            for x in range(MATRIX_SIZE):
                r, g, b = image.getpixel((x, y))
                # Convert RGB to grayscale and choose character
                gray = int(0.299*r + 0.587*g + 0.114*b)
                if gray > 200:
                    row += "█"
                elif gray > 150:
                    row += "▓"
                elif gray > 100:
                    row += "▒"
                elif gray > 50:
                    row += "░"
                else:
                    row += " "
            print(row)
        print("="*50)

    def run_visualizer(self):
        """Main visualizer loop"""
        print("Starting Spotify Visualizer...")
        
        # Check for saved tokens first
        if not self.load_saved_tokens():
            print("No saved tokens found. Starting authentication...")
            auth_url = self.get_authorization_url()
            
            print(f"\n🌐 Opening browser for Spotify authorization...")
            print(f"If the browser doesn't open automatically, visit:")
            print(f"{auth_url}\n")
            
            # Try to open browser
            try:
                webbrowser.open(auth_url)
            except:
                print("Could not open browser automatically")
            
            # Start callback server
            if not self.start_callback_server():
                print("❌ Authentication failed!")
                return
            
            # Wait for and read the authorization code
            try:
                with open('.auth_code', 'r') as f:
                    code = f.read().strip()
                os.remove('.auth_code')  # Clean up
            except FileNotFoundError:
                print("❌ No authorization code received")
                return
            
            if not self.exchange_code_for_token(code):
                print("❌ Token exchange failed!")
                return
        
        print("Starting visualizer loop...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                track_data = self.get_current_track()
                
                if track_data and track_data.get('item'):
                    track = track_data['item']
                    album = track.get('album', {})
                    images = album.get('images', [])
                    
                    if images:
                        image_url = images[0]['url']  # Get highest resolution image
                        print(f"Now playing: {track['name']} by {track['artists'][0]['name']}")
                        
                        # Process and display image
                        processed_image = self.download_and_process_image(image_url)
                        if processed_image:
                            self.display_image_on_matrix(processed_image)
                        else:
                            print("Failed to process album art")
                    else:
                        print("No album art available")
                else:
                    print("No track currently playing")
                
                time.sleep(REFRESH_INTERVAL)
                
        except KeyboardInterrupt:
            print("\nVisualizer stopped by user")
        except Exception as e:
            print(f"Error in visualizer loop: {e}")

def main():
    visualizer = SpotifyVisualizer()
    visualizer.run_visualizer()

if __name__ == "__main__":
    main()
