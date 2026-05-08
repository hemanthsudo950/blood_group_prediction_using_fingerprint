#!/usr/bin/env python3
"""
Quick Setup Script - Run this to get started quickly
"""

import os
import sys
import subprocess

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("✅ Dependencies installed!")

def create_database():
    """Create fingerprint database"""
    print("\n📋 Creating database from fingerprints...")
    subprocess.check_call([sys.executable, "auto_db.py"])
    print("✅ Database created!")

def start_server():
    """Start Flask server"""
    print("\n🚀 Starting BloodSense Advanced...")
    print("📍 Access at: http://localhost:5000")
    print("Press Ctrl+C to stop\n")
    subprocess.call([sys.executable, "app.py"])

if __name__ == "__main__":
    try:
        install_dependencies()
        create_database()
        start_server()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
