#!/usr/bin/env python3
"""
Launcher script for Medical Image Analysis System
"""
import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def check_dependencies():
    """Check if required packages are installed"""
    required = ['streamlit', 'pandas', 'numpy', 'plotly', 'bcrypt']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    return missing

def install_dependencies():
    """Install missing dependencies"""
    print("Installing required dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def create_directories():
    """Create necessary directories"""
    directories = [
        'database',
        'logs',
        'assets/images',
        'pages',
        'modules'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✓ Directory structure created")

def init_database():
    """Initialize database"""
    try:
        from database import DatabaseManager
        db = DatabaseManager()
        print("✓ Database initialized")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")

def main():
    """Main launcher function"""
    print("=" * 60)
    print("MEDICAL IMAGE ANALYSIS SYSTEM")
    print("=" * 60)
    print(f"Version: 1.0.0")
    print(f"Author: Eric Nyaga Kivuti (B141/24868/2022)")
    print(f"University of Embu")
    print("=" * 60)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("✗ Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Check dependencies
    missing = check_dependencies()
    if missing:
        print(f"Missing dependencies: {', '.join(missing)}")
        response = input("Install missing dependencies? (y/n): ")
        if response.lower() == 'y':
            install_dependencies()
        else:
            print("Please install dependencies manually and try again.")
            sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Initialize database
    init_database()
    
    print("\n" + "=" * 60)
    print("Starting Medical Image Analysis System...")
    print("=" * 60)
    
    # Get the absolute path to app.py
    app_path = Path(__file__).parent / "app.py"
    
    # Start Streamlit
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]
    
    # Open browser after a short delay
    def open_browser():
        time.sleep(3)
        webbrowser.open("http://localhost:8501")
    
    import threading
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run Streamlit
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()