#!/usr/bin/env python3
"""
Serial Debugger Launcher Script

This script starts both the backend server and opens the frontend in a browser.
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path


def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import serial
        import click
        return True
    except ImportError:
        print("Dependencies not installed. Installing...")
        return False


def install_dependencies():
    """Install required dependencies"""
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])


def start_backend():
    """Start the FastAPI backend server"""
    print("Starting Serial Debugger Backend...")
    print("API URL: http://localhost:8000")
    print("API Docs: http://localhost:8000/api/docs")
    print("")
    
    # Start uvicorn server
    process = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "backend.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ], cwd=os.path.dirname(os.path.abspath(__file__)))
    
    return process


def open_frontend():
    """Open the frontend in browser"""
    frontend_path = Path(__file__).parent / "frontend" / "dist" / "index.html"

    if frontend_path.exists():
        # Open via backend server (avoids file:// protocol asset path issues)
        webbrowser.open("http://localhost:8000")
    else:
        # Open API docs if frontend not built
        time.sleep(2)
        webbrowser.open("http://localhost:8000/api/docs")


def main():
    """Main entry point"""
    print("=" * 60)
    print("Serial Debugger - XCOM V2.6 Compatible")
    print("=" * 60)
    print("")
    
    # Check and install dependencies
    if not check_dependencies():
        try:
            install_dependencies()
        except subprocess.CalledProcessError as e:
            print(f"Failed to install dependencies: {e}")
            sys.exit(1)
    
    # Start backend
    backend_process = start_backend()
    
    # Wait for server to start
    time.sleep(3)
    
    # Open frontend
    open_frontend()
    
    print("Press Ctrl+C to stop the server")
    print("")
    
    try:
        # Wait for backend process
        backend_process.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
        backend_process.terminate()
        backend_process.wait()
        print("Goodbye!")


if __name__ == "__main__":
    main()
