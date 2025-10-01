#!/usr/bin/env python3
"""
Local Development Server Starter for Visey Recommender
Starts the server with proper configuration for local testing.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def setup_environment():
    """Setup environment variables for local development"""
    env_vars = {
        # WordPress (using demo site for testing)
        "WP_BASE_URL": "https://demo.wp-api.org",
        "WP_AUTH_TYPE": "none",
        "WP_SYNC_INTERVAL": "5",  # 5 minutes for testing
        "WP_CACHE_FALLBACK": "true",
        "WP_RATE_LIMIT": "30",
        "WP_TIMEOUT": "10",
        "WP_BATCH_SIZE": "50",
        
        # Cache
        "CACHE_BACKEND": "sqlite",  # Use SQLite for local testing
        "REDIS_URL": "",  # Empty to use SQLite
        
        # Service
        "TOP_N": "10",
        "DATA_DIR": "./data",
        
        # Weights
        "CONTENT_WEIGHT": "0.6",
        "COLLAB_WEIGHT": "0.3",
        "POP_WEIGHT": "0.1",
        "EMB_WEIGHT": "0.0",
        
        # Development
        "ENVIRONMENT": "development",
        "LOG_LEVEL": "INFO"
    }
    
    print("🔧 Setting up environment variables...")
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"   {key}={value}")
    
    # Create data directory
    data_dir = Path("./data")
    data_dir.mkdir(exist_ok=True)
    print(f"📁 Created data directory: {data_dir.absolute()}")

def check_dependencies():
    """Check if required dependencies are installed"""
    print("📦 Checking dependencies...")
    
    try:
        import fastapi
        import uvicorn
        import httpx
        import pydantic
        import numpy
        print("✅ Core dependencies found")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    return True

def start_server():
    """Start the development server"""
    print("🚀 Starting Visey Recommender server...")
    print("   URL: http://localhost:8000")
    print("   Docs: http://localhost:8000/docs")
    print("   Health: http://localhost:8000/health")
    print("\n   Press Ctrl+C to stop the server\n")
    
    try:
        # Start with uvicorn
        cmd = [
            sys.executable, "-m", "uvicorn",
            "visey_recommender.api.main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--log-level", "info"
        ]
        
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return False
    
    return True

def main():
    """Main function"""
    print("=" * 60)
    print("🎯 VISEY RECOMMENDER LOCAL DEVELOPMENT SERVER")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Setup environment
    setup_environment()
    
    # Start server
    if not start_server():
        sys.exit(1)

if __name__ == "__main__":
    main()