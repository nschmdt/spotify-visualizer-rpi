#!/usr/bin/env python3
"""
Setup script for Spotify LED Matrix Visualizer
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def main():
    print("🚀 Setting up Spotify LED Matrix Visualizer")
    print("=" * 50)
    
    # Check if we're on Raspberry Pi
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            if 'BCM' in cpuinfo:
                print("✅ Raspberry Pi detected")
                is_pi = True
            else:
                print("⚠️  Not running on Raspberry Pi - will use simulation mode")
                is_pi = False
    except:
        print("⚠️  Could not detect platform - will use simulation mode")
        is_pi = False
    
    # Install Python dependencies
    if not run_command("pip3 install -r requirements.txt", "Installing Python dependencies"):
        print("❌ Failed to install dependencies. Please check your Python/pip installation.")
        return False
    
    # Install RGB matrix library if on Pi
    if is_pi:
        print("\n🔧 Installing RGB matrix library for Raspberry Pi...")
        
        # Update system packages
        run_command("sudo apt update", "Updating system packages")
        
        # Install required system packages
        run_command("sudo apt install -y python3-dev python3-pip libfreetype6-dev libjpeg-dev zlib1g-dev", 
                   "Installing system dependencies")
        
        # Install RGB matrix library
        if not run_command("pip3 install rpi-rgb-led-matrix", "Installing RGB matrix library"):
            print("⚠️  RGB matrix library installation failed. You may need to install it manually.")
            print("   Visit: https://github.com/hzeller/rpi-rgb-led-matrix")
    
    # Make scripts executable
    run_command("chmod +x spotify_visualizer.py", "Making main script executable")
    run_command("chmod +x callback_server.py", "Making callback server executable")
    run_command("chmod +x setup.py", "Making setup script executable")
    
    print("\n" + "=" * 50)
    print("✅ Setup completed!")
    print("\nNext steps:")
    print("1. Update CLIENT_ID in spotify_visualizer.py with your Spotify app credentials")
    print("2. Run: python3 spotify_visualizer.py")
    print("3. Follow the authentication prompts")
    print("\nFor auto-startup on boot, see the systemd service file.")
    
    return True

if __name__ == "__main__":
    main()
