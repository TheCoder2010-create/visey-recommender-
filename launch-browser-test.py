#!/usr/bin/env python3
"""
Browser Test Launcher for Visey Recommender
Starts API server, frontend server, and opens browser automatically
"""

import os
import sys
import time
import subprocess
import threading
import webbrowser
from pathlib import Path

def start_api_server():
    """Start the test API server."""
    print("🚀 Starting Test API Server...")
    
    try:
        # Start the simple test API
        process = subprocess.Popen([
            sys.executable, "test-frontend-simple.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
           universal_newlines=True, bufsize=1)
        
        # Monitor output
        def monitor():
            for line in iter(process.stdout.readline, ''):
                print(f"[API] {line.strip()}")
        
        threading.Thread(target=monitor, daemon=True).start()
        return process
        
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        return None

def start_frontend_server():
    """Start the frontend server."""
    print("🌐 Starting Frontend Server...")
    
    try:
        frontend_dir = Path("frontend")
        
        process = subprocess.Popen([
            sys.executable, "server.py"
        ], cwd=frontend_dir, stdout=subprocess.PIPE, 
           stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1)
        
        # Monitor output
        def monitor():
            for line in iter(process.stdout.readline, ''):
                print(f"[Frontend] {line.strip()}")
        
        threading.Thread(target=monitor, daemon=True).start()
        return process
        
    except Exception as e:
        print(f"❌ Failed to start frontend server: {e}")
        return None

def wait_for_server(url, timeout=30):
    """Wait for server to be ready."""
    import requests
    
    for i in range(timeout):
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                return True
        except:
            pass
        time.sleep(1)
    return False

def open_browser():
    """Open the application in browser."""
    print("🌐 Opening browser...")
    
    try:
        # Try different browsers
        browsers = [
            'chrome',
            'firefox', 
            'edge',
            'safari',
            None  # Default browser
        ]
        
        for browser_name in browsers:
            try:
                if browser_name:
                    browser = webbrowser.get(browser_name)
                else:
                    browser = webbrowser
                
                browser.open('http://localhost:3000')
                print(f"✅ Opened in {browser_name or 'default browser'}")
                return True
            except:
                continue
        
        print("⚠️  Could not open browser automatically")
        print("   Please open http://localhost:3000 manually")
        return False
        
    except Exception as e:
        print(f"⚠️  Browser error: {e}")
        return False

def main():
    """Main launcher function."""
    print("=" * 60)
    print("🧠 Visey Recommender - Browser Test Launcher")
    print("=" * 60)
    
    api_process = None
    frontend_process = None
    
    try:
        # Start API server
        api_process = start_api_server()
        if not api_process:
            return False
        
        # Wait for API to be ready
        print("⏳ Waiting for API server...")
        if not wait_for_server("http://localhost:8000/health", 15):
            print("❌ API server failed to start")
            return False
        
        print("✅ API server is ready!")
        
        # Start frontend server
        frontend_process = start_frontend_server()
        if not frontend_process:
            return False
        
        # Wait for frontend to be ready
        print("⏳ Waiting for frontend server...")
        time.sleep(3)  # Give frontend time to start
        
        print("✅ Frontend server is ready!")
        
        # Open browser
        open_browser()
        
        print("=" * 60)
        print("🎉 Visey Recommender is now running!")
        print("")
        print("🌐 Frontend:  http://localhost:3000")
        print("📊 API:      http://localhost:8000")
        print("📋 API Docs: http://localhost:8000/docs")
        print("")
        print("🎯 How to test:")
        print("1. The browser should open automatically")
        print("2. Try getting recommendations for User ID: 1")
        print("3. Test the search functionality")
        print("4. Check the system status dashboard")
        print("5. Try the performance testing tools")
        print("")
        print("💡 Tips:")
        print("- Toggle 'Demo Mode' if you see connection errors")
        print("- All test data is built-in, no WordPress needed")
        print("- Check browser console (F12) for any errors")
        print("")
        print("⏹️  Press Ctrl+C to stop both servers")
        print("=" * 60)
        
        # Keep running
        try:
            while True:
                time.sleep(1)
                
                # Check if processes are still running
                if api_process.poll() is not None:
                    print("❌ API server stopped")
                    break
                    
                if frontend_process.poll() is not None:
                    print("❌ Frontend server stopped")
                    break
        
        except KeyboardInterrupt:
            print("\n⏹️  Stopping servers...")
        
    finally:
        # Cleanup
        if api_process:
            api_process.terminate()
            try:
                api_process.wait(timeout=5)
            except:
                api_process.kill()
        
        if frontend_process:
            frontend_process.terminate()
            try:
                frontend_process.wait(timeout=5)
            except:
                frontend_process.kill()
        
        print("✅ Servers stopped")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)