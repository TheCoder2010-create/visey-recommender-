#!/usr/bin/env python3
"""
Startup script for Visey Recommender with Frontend
Launches both the API server and frontend server
"""

import os
import sys
import time
import signal
import subprocess
import threading
import webbrowser
from pathlib import Path

class ViseyLauncher:
    def __init__(self):
        self.api_process = None
        self.frontend_process = None
        self.running = True
        
    def start_api_server(self):
        """Start the FastAPI server."""
        print("🚀 Starting Visey Recommender API server...")
        
        try:
            # Start API server
            cmd = [
                sys.executable, "-m", "uvicorn", 
                "visey_recommender.api.main:app",
                "--reload",
                "--host", "0.0.0.0",
                "--port", "8000"
            ]
            
            self.api_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            print("✅ API server started on http://localhost:8000")
            
            # Monitor API server output
            def monitor_api():
                for line in iter(self.api_process.stdout.readline, ''):
                    if self.running:
                        print(f"[API] {line.strip()}")
                    else:
                        break
            
            threading.Thread(target=monitor_api, daemon=True).start()
            
        except Exception as e:
            print(f"❌ Failed to start API server: {e}")
            return False
            
        return True
    
    def start_frontend_server(self):
        """Start the frontend server."""
        print("🌐 Starting frontend server...")
        
        try:
            frontend_dir = Path(__file__).parent / "frontend"
            
            # Start frontend server
            cmd = [sys.executable, "server.py"]
            
            self.frontend_process = subprocess.Popen(
                cmd,
                cwd=frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            print("✅ Frontend server started on http://localhost:3000")
            
            # Monitor frontend server output
            def monitor_frontend():
                for line in iter(self.frontend_process.stdout.readline, ''):
                    if self.running:
                        print(f"[Frontend] {line.strip()}")
                    else:
                        break
            
            threading.Thread(target=monitor_frontend, daemon=True).start()
            
        except Exception as e:
            print(f"❌ Failed to start frontend server: {e}")
            return False
            
        return True
    
    def wait_for_api(self, timeout=30):
        """Wait for API server to be ready."""
        import requests
        
        print("⏳ Waiting for API server to be ready...")
        
        for i in range(timeout):
            try:
                response = requests.get("http://localhost:8000/health", timeout=2)
                if response.status_code == 200:
                    print("✅ API server is ready!")
                    return True
            except:
                pass
            
            time.sleep(1)
            if i % 5 == 0:
                print(f"   Still waiting... ({i}/{timeout}s)")
        
        print("❌ API server failed to start within timeout")
        return False
    
    def open_browser(self):
        """Open the frontend in the default browser."""
        try:
            time.sleep(2)  # Give frontend server time to start
            webbrowser.open('http://localhost:3000')
            print("🌐 Opened frontend in browser")
        except Exception as e:
            print(f"⚠️  Could not open browser: {e}")
            print("   Please open http://localhost:3000 manually")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            print(f"\n⏹️  Received signal {signum}, shutting down...")
            self.shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def shutdown(self):
        """Shutdown both servers."""
        print("🛑 Shutting down servers...")
        self.running = False
        
        if self.api_process:
            print("   Stopping API server...")
            self.api_process.terminate()
            try:
                self.api_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.api_process.kill()
        
        if self.frontend_process:
            print("   Stopping frontend server...")
            self.frontend_process.terminate()
            try:
                self.frontend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.frontend_process.kill()
        
        print("✅ Shutdown complete")
    
    def run(self):
        """Main run method."""
        print("=" * 60)
        print("🧠 Visey Recommender - Full Stack Launcher")
        print("=" * 60)
        
        # Setup signal handlers
        self.setup_signal_handlers()
        
        # Check prerequisites
        try:
            import uvicorn
            import fastapi
            import requests
        except ImportError as e:
            print(f"❌ Missing required package: {e}")
            print("   Please run: pip install -r requirements.txt")
            return False
        
        # Start API server
        if not self.start_api_server():
            return False
        
        # Wait for API to be ready
        if not self.wait_for_api():
            self.shutdown()
            return False
        
        # Start frontend server
        if not self.start_frontend_server():
            self.shutdown()
            return False
        
        # Open browser
        threading.Thread(target=self.open_browser, daemon=True).start()
        
        print("=" * 60)
        print("🎉 Visey Recommender is now running!")
        print("")
        print("📊 API Server:      http://localhost:8000")
        print("   - Health:        http://localhost:8000/health")
        print("   - Docs:          http://localhost:8000/docs")
        print("   - Metrics:       http://localhost:8000/metrics")
        print("")
        print("🌐 Frontend:        http://localhost:3000")
        print("   - Test Interface: Full-featured testing UI")
        print("   - Real-time monitoring and testing")
        print("")
        print("⚙️  Configuration:")
        print(f"   - WordPress URL: {os.getenv('WP_BASE_URL', 'Not configured')}")
        print(f"   - Auth Type:     {os.getenv('WP_AUTH_TYPE', 'none')}")
        print(f"   - Cache Backend: {os.getenv('CACHE_BACKEND', 'auto')}")
        print("")
        print("📋 Quick Start:")
        print("   1. Open http://localhost:3000 in your browser")
        print("   2. Check system status in the dashboard")
        print("   3. Test recommendations with user ID 1")
        print("   4. Explore WordPress data and sync options")
        print("")
        print("⏹️  Press Ctrl+C to stop both servers")
        print("=" * 60)
        
        try:
            # Keep the main thread alive
            while self.running:
                time.sleep(1)
                
                # Check if processes are still running
                if self.api_process and self.api_process.poll() is not None:
                    print("❌ API server stopped unexpectedly")
                    break
                    
                if self.frontend_process and self.frontend_process.poll() is not None:
                    print("❌ Frontend server stopped unexpectedly")
                    break
        
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()
        
        return True

def main():
    """Main entry point."""
    launcher = ViseyLauncher()
    success = launcher.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()