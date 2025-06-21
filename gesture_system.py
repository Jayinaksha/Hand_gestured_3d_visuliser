#!/usr/bin/env python3
"""
Gesture Recognition System
Handles both basic and advanced hand gesture recognition
"""

import numpy as np
import time

class GestureSystem:
    def __init__(self):
        self.current_gesture = "none"
        self.gesture_confidence = {}
        self.gesture_history = []
        self.max_history = 10
        self.last_gesture_time = 0
        self.gesture_cooldown = 1.0  # seconds
        
    def detect_gesture(self, landmarks, hand_idx=0):
        """Detect basic hand gestures"""
        if not landmarks:
            return "none"
        
        # Extract key points
        wrist = np.array([landmarks[0][0], landmarks[0][1]])
        thumb_tip = np.array([landmarks[4][0], landmarks[4][1]])
        thumb_mcp = np.array([landmarks[2][0], landmarks[2][1]])
        index_tip = np.array([landmarks[8][0], landmarks[8][1]])
        index_pip = np.array([landmarks[6][0], landmarks[6][1]])
        middle_tip = np.array([landmarks[12][0], landmarks[12][1]])
        middle_pip = np.array([landmarks[10][0], landmarks[10][1]])
        ring_tip = np.array([landmarks[16][0], landmarks[16][1]])
        ring_pip = np.array([landmarks[14][0], landmarks[14][1]])
        pinky_tip = np.array([landmarks[20][0], landmarks[20][1]])
        pinky_pip = np.array([landmarks[18][0], landmarks[18][1]])
        
        # Check if fingers are extended
        thumb_extended = self.is_thumb_extended(landmarks)
        index_extended = index_tip[1] < index_pip[1] 
        middle_extended = middle_tip[1] < middle_pip[1]
        ring_extended = ring_tip[1] < ring_pip[1]
        pinky_extended = pinky_tip[1] < pinky_pip[1]
        
        # Calculate pinch distance
        pinch_distance = np.sqrt(np.sum((thumb_tip - index_tip) ** 2))
        is_pinching = pinch_distance < 0.05  # Threshold for pinch detection
        
        # Store finger states
        finger_states = [thumb_extended, index_extended, middle_extended, ring_extended, pinky_extended]
        
        # Recognize gestures with confidence scores
        confidences = {
            "fist": 0,
            "thumbs_up": 0,
            "peace": 0,
            "open_palm": 0,
            "pinch": 0,
            "rock_sign": 0
        }
        
        # FIST: All fingers closed
        if sum(finger_states) <= 1:
            confidences["fist"] = 0.8
            
        # THUMBS UP: Only thumb extended
        if thumb_extended and not index_extended and not middle_extended and not ring_extended and not pinky_extended:
            confidences["thumbs_up"] = 0.9
            
        # PEACE: Index and middle fingers extended, others closed
        if not thumb_extended and index_extended and middle_extended and not ring_extended and not pinky_extended:
            confidences["peace"] = 0.9
            
        # OPEN PALM: All fingers extended
        if sum(finger_states) >= 4:
            confidences["open_palm"] = 0.9
            
        # PINCH: Thumb and index close together
        if is_pinching:
            confidences["pinch"] = 0.8
            
        # ROCK SIGN: Index, pinky extended (and maybe thumb)
        if index_extended and not middle_extended and not ring_extended and pinky_extended:
            confidences["rock_sign"] = 0.8
            
        # Update the gesture confidence history
        self.gesture_confidence = confidences
        
        # Return the gesture with highest confidence
        best_gesture = max(confidences.items(), key=lambda x: x[1])
        if best_gesture[1] > 0.5:  # Threshold for detection
            gesture = best_gesture[0]
            
            # Add to history with timestamp
            now = time.time()
            if now - self.last_gesture_time > self.gesture_cooldown:
                self.gesture_history.append((gesture, now))
                if len(self.gesture_history) > self.max_history:
                    self.gesture_history.pop(0)
                self.last_gesture_time = now
                
            return gesture
        
        return "unknown"
    
    def is_thumb_extended(self, landmarks):
        """Special function to detect if thumb is extended"""
        thumb_tip = landmarks[4]
        thumb_mcp = landmarks[2]
        wrist = landmarks[0]
        
        try:
            # Calculate vectors
            wrist_to_mcp = np.array([thumb_mcp[0] - wrist[0], thumb_mcp[1] - wrist[1]])
            mcp_to_tip = np.array([thumb_tip[0] - thumb_mcp[0], thumb_tip[1] - thumb_mcp[1]])
            
            # Normalize vectors
            wrist_to_mcp_norm = np.linalg.norm(wrist_to_mcp)
            mcp_to_tip_norm = np.linalg.norm(mcp_to_tip)
            
            if wrist_to_mcp_norm > 0 and mcp_to_tip_norm > 0:
                wrist_to_mcp = wrist_to_mcp / wrist_to_mcp_norm
                mcp_to_tip = mcp_to_tip / mcp_to_tip_norm
                
                # Dot product tells us alignment
                dot_product = np.dot(wrist_to_mcp, mcp_to_tip)
                
                # If thumb is extended, vectors will be roughly aligned
                return dot_product > 0.7  # Threshold for thumb extension
        except:
            pass
            
        return False
        
    def get_gesture_name(self, gesture_code):
        """Get human-readable gesture name"""
        names = {
            "fist": "FIST",
            "peace": "PEACE", 
            "open_palm": "OPEN PALM",
            "pinch": "PINCH",
            "thumbs_up": "THUMBS UP",
            "rock_sign": "ROCK SIGN"
        }
        
        return names.get(gesture_code, gesture_code.upper())