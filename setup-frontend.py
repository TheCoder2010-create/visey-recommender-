#!/usr/bin/env python3
"""
Quick setup script for Visey Recommender Frontend
Checks dependencies and provides setup instructions
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_dependencies():
    """Check if required packages are installed."""
    required_packages = [
        'fastapi',
        'uvicorn',
        'httpx',
        'pydantic',
        'redis',
        'structlog',
        'prometheus-client'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    return missing_packages

def install_dependencies(missing_packages):
    """Install missing dependencies."""
    if not missing_packages:
        return True
    
    print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_ports():
    """Check if required ports are available."""
    import socket
    
    ports_to_check = [8000, 3000]
    
    for port in ports_to_check:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:
            print(f"⚠️  Port {port} is already in use")
            if port == 8000:
                print("   This might be the API server already running")
            elif port == 3000:
                print("   This might be the frontend server already running")
        else:
            print(f"✅ Port {port} is available")

def create_env_file():
    """Create a sample .env file if it doesn't exist."""
    env_file = Path(".env")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return
    
    sample_env = """# Visey Recommender Configuration

# WordPress API Settings
WP_BASE_URL=https://your-wordpress-site.com
WP_AUTH_TYPE=none
WP_USERNAME=your_username
WP_PASSWORD=your_password

# Cache Settings
CACHE_BACKEND=auto
REDIS_URL=redis://localhost:6379

# Recommendation Settings
TOP_N=10
CONTENT_WEIGHT=0.6
COLLAB_WEIGHT=0.3
POP_WEIGHT=0.1

# WordPress Sync Settings
WP_SYNC_INTERVAL=30
WP_CACHE_FALLBACK=true
WP_RATE_LIMIT=60
WP_BATCH_SIZE=100
"""
    
    try:
        env_file.write_text(sample_env)
        print("✅ Created sample .env file")
        print("   Please update it with your WordPress credentials")
    except Exception as e:
        print(f"⚠️  Could not create .env file: {e}")

def main():
    """Main setup function."""
    print("🚀 Visey Recommender Frontend Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    print("\n📦 Checking dependencies...")
    missing_packages = check_dependencies()
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        
        install = input("\n📥 Install missing packages? (y/N): ").lower().strip()
        if install in ['y', 'yes']:
            if not install_dependencies(missing_packages):
                return False
        else:
            print("⚠️  Please install missing packages manually:")
            print("   pip install -r requirements.txt")
            return False
    
    print("\n🔌 Checking ports...")
    check_ports()
    
    print("\n⚙️  Setting up configuration...")
    create_env_file()
    
    print("\n" + "=" * 50)
    print("✅ Setup completed successfully!")
    print("\n🎯 Next steps:")
    print("1. Update .env file with your WordPress credentials (optional)")
    print("2. Start the full stack:")
    print("   python start-frontend.py")
    print("\n   OR start components separately:")
    print("   python -m uvicorn visey_recommender.api.main:app --reload")
    print("   cd frontend && python server.py")
    print("\n🌐 URLs:")
    print("   Frontend: http://localhost:3000")
    print("   API:      http://localhost:8000")
    print("   API Docs: http://localhost:8000/docs")
    print("\n💡 Tips:")
    print("   - Use Demo Mode if WordPress is not available")
    print("   - Check the frontend README.md for detailed usage")
    print("   - Monitor logs for troubleshooting")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)