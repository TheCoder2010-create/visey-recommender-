#!/usr/bin/env python3
"""Simple HTTP server for Visey Recommender frontend."""

import os
import sys
import http.server
import socketserver
import webbrowser
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler with CORS support."""
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def main():
    """Start the frontend server."""
    # Change to frontend directory
    frontend_dir = Path(__file__).parent
    os.chdir(frontend_dir)
    
    # Configuration
    PORT = 3000
    HOST = 'localhost'
    
    print(f"🚀 Starting Visey Recommender Frontend Server")
    print(f"📁 Serving from: {frontend_dir}")
    print(f"🌐 URL: http://{HOST}:{PORT}")
    print(f"📋 Make sure the API server is running on http://localhost:8000")
    print(f"⏹️  Press Ctrl+C to stop the server")
    print("-" * 60)
    
    try:
        # Create server
        with socketserver.TCPServer((HOST, PORT), CORSHTTPRequestHandler) as httpd:
            print(f"✅ Server started successfully on port {PORT}")
            
            # Open browser
            try:
                webbrowser.open(f'http://{HOST}:{PORT}')
                print(f"🌐 Opened browser automatically")
            except Exception as e:
                print(f"⚠️  Could not open browser automatically: {e}")
                print(f"   Please open http://{HOST}:{PORT} manually")
            
            print("-" * 60)
            
            # Start serving
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print(f"\n⏹️  Server stopped by user")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {PORT} is already in use")
            print(f"   Please stop any other servers on port {PORT} or change the PORT variable")
        else:
            print(f"❌ Server error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()