# run_weather_app.py
"""
Launcher for the Weather App
Run this file to start the application
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import and run the controller
from bridge import main

if __name__ == "__main__":
    main() 
