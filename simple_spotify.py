#!/usr/bin/env python3
import time
import requests
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image
import io

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
    options.brightness = 80    # Much brighter! (was default ~50)
    options.pwm_bits = 8       # Better color depth
    options.pwm_lsb_nanoseconds = 200  # Smoother display
    return RGBMatrix(options=options)

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

def main():
    print("Simple Spotify Visualizer")
    print("=" * 40)
    
    # Setup matrix
    matrix = setup_matrix()
    print(" RGB Matrix initialized")
    
    # Get authorization URL
    auth_url, code_verifier = get_authorization_url()
    
    print(f"\n Please visit this URL in your browser:")
    print(f"{auth_url}\n")
    
    print("After logging in, you'll be redirected to a page that says 'can't connect'")
    print("That's normal! Copy the 'code' parameter from the URL and paste it here:")
    
    # Get the code from user
    code = input("Enter the authorization code: ").strip()
    
    if not code:
        print("No code provided. Exiting.")
        return
    
    # Exchange code for token
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
        access_token = token_data['access_token']
        print("✅ Successfully authenticated with Spotify!")
        
        # Start the visualizer loop
        print("Starting visualizer loop...")
        while True:
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get('https://api.spotify.com/v1/me/player/currently-playing', headers=headers)
            
            if response.status_code == 200:
                track_data = response.json()
                if track_data and track_data.get('item'):
                    track = track_data['item']
                    album = track.get('album', {})
                    images = album.get('images', [])
                    
                    if images:
                        image_url = images[0]['url']
                        print(f"Now playing: {track['name']} by {track['artists'][0]['name']}")
                        
                        # Download and display image
                        try:
                            img_response = requests.get(image_url, timeout=10)
                            if img_response.status_code == 200:
                                image = Image.open(io.BytesIO(img_response.content))
                                if image.mode != 'RGB':
                                    image = image.convert('RGB')
                                image = image.resize((MATRIX_SIZE, MATRIX_SIZE), Image.Resampling.LANCZOS)
                                
                                # Display on matrix
                                for y in range(MATRIX_SIZE):
                                    for x in range(MATRIX_SIZE):
                                        r, g, b = image.getpixel((x, y))
                                        matrix.SetPixel(x, y, r, g, b)
                        except Exception as e:
                            print(f"Error processing image: {e}")
                    else:
                        print("No album art available")
                else:
                    print("No track currently playing")
            else:
                print("No track currently playing")
            
            time.sleep(1)
    else:
        print(f" Authentication failed: {response.status_code} - {response.text}")

if __name__ == "__main__":
    main()