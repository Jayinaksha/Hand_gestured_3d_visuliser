#!/usr/bin/env python3
"""
Iron Man Hand Gesture 3D Controller - Main Entry Point
"""

from controller import IronManController

if __name__ == "__main__":
    print("Starting Iron Man Hand Gesture CAD System...")
    try:
        controller = IronManController()
        controller.run()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        print("Application crashed. Please check error messages above.")