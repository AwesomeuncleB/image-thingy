#!/usr/bin/env python3
"""
Startup script for the Event Face Detection API
"""

import subprocess
import sys
import os
import time
import requests
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import numpy
        from PIL import Image
        print("✓ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def start_api_server(host="127.0.0.1", port=8000, reload=True):
    """Start the FastAPI server"""
    print(f"Starting Face Detection API server on {host}:{port}")
    
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "main:app", 
        "--host", host, 
        "--port", str(port)
    ]
    
    if reload:
        cmd.append("--reload")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start server: {e}")

def wait_for_api(url="http://localhost:8000", timeout=30):
    """Wait for API to be ready"""
    print("Waiting for API to be ready...")
    
    for i in range(timeout):
        try:
            response = requests.get(f"{url}/health", timeout=1)
            if response.status_code == 200:
                print("✓ API is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(1)
        if i % 5 == 0:
            print(f"Still waiting... ({i}/{timeout}s)")
    
    print("❌ API failed to start within timeout")
    return False

def run_tests():
    """Run API tests"""
    print("Running API tests...")
    try:
        subprocess.run([sys.executable, "test_api.py"], check=True)
        print("✓ All tests passed!")
    except subprocess.CalledProcessError:
        print("❌ Some tests failed")

def main():
    """Main startup function"""
    print("🚀 Event Face Detection API Startup")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Create necessary directories
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Start Event Face Detection API")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    parser.add_argument("--test", action="store_true", help="Run tests after starting")
    
    args = parser.parse_args()
    
    if args.test:
        # Start server in background and run tests
        import threading
        import signal
        
        server_process = None
        
        def signal_handler(sig, frame):
            if server_process:
                server_process.terminate()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Start server in separate thread
        server_thread = threading.Thread(
            target=start_api_server,
            args=(args.host, args.port, not args.no_reload),
            daemon=True
        )
        server_thread.start()
        
        # Wait for API and run tests
        if wait_for_api(f"http://{args.host}:{args.port}"):
            run_tests()
        
    else:
        # Start server normally
        start_api_server(args.host, args.port, not args.no_reload)

if __name__ == "__main__":
    main()