#!/usr/bin/env python3
"""
🔥 Test if everything is working on Ubuntu 24.04
"""

import sys
print("🚀 Testing Hand Gesture 3D Creator Setup...")
print(f"Python version: {sys.version}")

# Test 1: OpenCV and Camera
try:
    import cv2
    print("✅ OpenCV imported successfully")
    print(f"OpenCV version: {cv2.__version__}")
    
    # Test camera
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        print("✅ Camera is working!")
        ret, frame = cap.read()
        if ret:
            print(f"✅ Camera frame captured: {frame.shape}")
        cap.release()
    else:
        print("❌ Camera not accessible")
except Exception as e:
    print(f"❌ OpenCV error: {e}")

# Test 2: MediaPipe
try:
    import mediapipe as mp
    print("✅ MediaPipe imported successfully")
    print(f"MediaPipe version: {mp.__version__}")
except Exception as e:
    print(f"❌ MediaPipe error: {e}")

# Test 3: Ursina (3D Engine)
try:
    from ursina import *
    print("✅ Ursina imported successfully")
except Exception as e:
    print(f"❌ Ursina error: {e}")

# Test 4: Pygame (Audio)
try:
    import pygame
    pygame.mixer.init()
    print("✅ Pygame audio initialized")
    print(f"Pygame version: {pygame.version.ver}")
except Exception as e:
    print(f"❌ Pygame error: {e}")

# Test 5: Numpy
try:
    import numpy as np
    print("✅ Numpy imported successfully")
    print(f"Numpy version: {np.__version__}")
except Exception as e:
    print(f"❌ Numpy error: {e}")

print("\n🎉 Setup test complete!")
print("If you see all ✅, you're ready to rock! 🔥")