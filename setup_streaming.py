"""
Quick setup guide for streaming live IoT data to dashboard

This file provides installation and setup instructions for streaming real-time
sensor data directly to the dashboard via WebSocket (no database save).
"""

import subprocess
import sys
import os

def setup_streaming():
    """Setup websockets package for streaming"""
    print("=" * 80)
    print("STREAMING IoT DATA SETUP")
    print("=" * 80)
    print()
    
    # Check if websockets is installed
    try:
        import websockets
        print("[OK] websockets already installed")
    except ImportError:
        print("[!] Installing websockets package...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
        print("[OK] websockets installed!")
    
    print()
    print("=" * 80)
    print("SETUP COMPLETE - HOW TO USE")
    print("=" * 80)
    print()
    
    print("Step 1: Start the backend webserver in Terminal 1:")
    print("   cd <project_folder>")
    print("   python -m uvicorn app.main:app --reload")
    print()
    
    print("Step 2: Start the data streamer in Terminal 2:")
    print("   cd <project_folder>")
    print("   python stream_iot_data_live.py")
    print()
    
    print("Step 3: Open dashboard in browser:")
    print("   http://localhost:5173  (or your frontend URL)")
    print()
    
    print("Features:")
    print("  - Real-time sensor data streams to dashboard")
    print("  - NO database save (pure live streaming)")
    print("  - 5 metrics per batch (temperature, humidity, soil, light, pressure)")
    print("  - Default: 5-second intervals")
    print()
    
    print("Custom options:")
    print("  python stream_iot_data_live.py --interval 10")
    print("  python stream_iot_data_live.py --server 192.168.1.100:8000")
    print()


if __name__ == "__main__":
    setup_streaming()
