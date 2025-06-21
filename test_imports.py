#!/usr/bin/env python3
"""
Test script to verify all imports work correctly
"""

print("Testing imports...")

try:
    import cv2
    print("✅ OpenCV imported successfully")
except ImportError as e:
    print(f"❌ OpenCV import failed: {e}")

try:
    import mediapipe as mp
    print("✅ MediaPipe imported successfully")
except ImportError as e:
    print(f"❌ MediaPipe import failed: {e}")

try:
    import numpy as np
    print("✅ NumPy imported successfully")
except ImportError as e:
    print(f"❌ NumPy import failed: {e}")

try:
    from scipy.spatial.transform import Rotation
    print("✅ SciPy imported successfully")
except ImportError as e:
    print(f"❌ SciPy import failed: {e}")

try:
    from filterpy.kalman import KalmanFilter
    print("✅ FilterPy imported successfully")
except ImportError as e:
    print(f"❌ FilterPy import failed: {e}")

try:
    from ursina import *
    print("✅ Ursina imported successfully")
except ImportError as e:
    print(f"❌ Ursina import failed: {e}")

try:
    import pygame
    print("✅ Pygame imported successfully")
except ImportError as e:
    print(f"❌ Pygame import failed: {e}")

print("\nTesting project modules...")

try:
    from precision_tracking import PrecisionHandTracker
    print("✅ PrecisionHandTracker imported successfully")
except ImportError as e:
    print(f"❌ PrecisionHandTracker import failed: {e}")

try:
    from gesture_system import GestureSystem
    print("✅ GestureSystem imported successfully")
except ImportError as e:
    print(f"❌ GestureSystem import failed: {e}")

try:
    from cad_system import CADSystem
    from controller import IronManController
    print("✅ Main controller components imported successfully")
except ImportError as e:
    print(f"❌ Main controller import failed: {e}")

print("\n🎉 All imports tested!")