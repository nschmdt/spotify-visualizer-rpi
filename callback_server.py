#!/usr/bin/env python3
"""
Simple HTTP server to handle Spotify OAuth callback
"""

import http.server
import socketserver
import urllib.parse
import webbrowser
import threading
import time

class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/callback'):
            # Parse the callback URL
            parsed_url = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            
            if 'code' in query_params:
                code = query_params['code'][0]
                print(f"\n✅ Authorization successful!")
                print(f"Code: {code}")
                print(f"\nCopy this code and paste it into the main script.")
                print("You can close this server now (Ctrl+C)")
                
                # Save code to file for automatic pickup
                with open('.auth_code', 'w') as f:
                    f.write(code)
            else:
                print(f"\n❌ No authorization code found in callback")
                print(f"URL: {self.path}")
            
            # Send response to browser
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'''
            <html>
            <body style="font-family: Arial; text-align: center; padding: 50px; background: #1DB954; color: white;">
                <h1>✅ Authorization Complete!</h1>
                <p>You can close this window and return to the terminal.</p>
                <p>The authorization code has been automatically captured.</p>
            </body>
            </html>
            ''')
        else:
            self.send_response(404)
            self.end_headers()

def start_callback_server(port=8080):
    """Start the callback server"""
    try:
        with socketserver.TCPServer(("", port), CallbackHandler) as httpd:
            print(f"Callback server started on port {port}")
            print("Waiting for Spotify authorization...")
            httpd.serve_forever()
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"Port {port} is already in use. Trying port {port + 1}")
            start_callback_server(port + 1)
        else:
            raise

if __name__ == "__main__":
    start_callback_server()
