#!/usr/bin/env python3
"""
Simple server starter for Visey Recommender testing
"""

import subprocess
import sys
import time
from pathlib import Path

def main():
    print("🚀 Starting Visey Recommender Test Servers")
    print("=" * 50)
    
    # Start API server in background
    print("1. Starting API server...")
    api_cmd = [sys.executable, "test-frontend-simple.py"]
    
    try:
        api_process = subprocess.Popen(api_cmd)
        print("✅ API server started (PID: {})".format(api_process.pid))
        print("   URL: http://localhost:8000")
        
        # Wait a moment for API to start
        time.sleep(3)
        
        # Start frontend server
        print("\n2. Starting frontend server...")
        frontend_dir = Path("frontend")
        frontend_cmd = [sys.executable, "server.py"]
        
        frontend_process = subprocess.Popen(frontend_cmd, cwd=frontend_dir)
        print("✅ Frontend server started (PID: {})".format(frontend_process.pid))
        print("   URL: http://localhost:3000")
        
        print("\n" + "=" * 50)
        print("🎉 Both servers are running!")
        print("\n📋 OPEN THESE URLS IN YOUR BROWSER:")
        print("🌐 Frontend Application: http://localhost:3000")
        print("📊 API Documentation:    http://localhost:8000/docs")
        print("🏥 API Health Check:     http://localhost:8000/health")
        
        print("\n🎯 Testing Instructions:")
        print("1. Open http://localhost:3000 in your browser")
        print("2. You should see the Visey Recommender interface")
        print("3. Try these tests:")
        print("   - Enter User ID: 1 and click 'Get Recommendations'")
        print("   - Search for 'scalable' in the search box")
        print("   - Check the system status dashboard")
        print("   - Try the WordPress sync button")
        
        print("\n💡 Troubleshooting:")
        print("- If you see connection errors, toggle 'Demo Mode' ON")
        print("- Check browser console (F12) for detailed errors")
        print("- Both servers must be running for full functionality")
        
        print("\n⏹️  To stop servers:")
        print("   Press Ctrl+C in this terminal")
        
        # Keep running until interrupted
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping servers...")
            api_process.terminate()
            frontend_process.terminate()
            print("✅ Servers stopped")
            
    except Exception as e:
        print(f"❌ Error starting servers: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()