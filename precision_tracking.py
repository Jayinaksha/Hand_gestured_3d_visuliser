#!/usr/bin/env python3
"""
Precision Hand Tracking Module for CAD Operations
Provides enhanced hand tracking capabilities for precise CAD manipulation
"""

import numpy as np
from scipy.spatial.transform import Rotation
from filterpy.kalman import KalmanFilter

class PrecisionHandTracker:
    def __init__(self):
        # Store previous frames for velocity calculation
        self.prev_landmarks = None
        self.landmark_history = []  # Last 5 frames for smoothing
        self.history_max = 5
        
        # Initialize Kalman filters for each fingertip
        self.filters = self._initialize_kalman_filters()
        
        # For precise gestures
        self.gesture_start_position = None
        self.gesture_start_time = None
        self.active_gestures = {}
        
        # For gesture history - helps with tool selection gestures
        self.gesture_history = []
        self.max_gesture_history = 10  # Store up to 10 recent gestures
        
    def _initialize_kalman_filters(self):
        """Create Kalman filters for smooth tracking"""
        filters = {}
        for i in [4, 8, 12, 16, 20]:  # Thumb, index, middle, ring, pinky tips
            kf = KalmanFilter(dim_x=6, dim_z=3)  # state: pos(3) + vel(3), measurement: pos(3)
            kf.F = np.array([
                [1, 0, 0, 1, 0, 0],  # x = x + vx
                [0, 1, 0, 0, 1, 0],  # y = y + vy
                [0, 0, 1, 0, 0, 1],  # z = z + vz
                [0, 0, 0, 1, 0, 0],  # vx = vx
                [0, 0, 0, 0, 1, 0],  # vy = vy
                [0, 0, 0, 0, 0, 1]   # vz = vz
            ])
            kf.H = np.array([
                [1, 0, 0, 0, 0, 0],
                [0, 1, 0, 0, 0, 0],
                [0, 0, 1, 0, 0, 0]
            ])
            kf.Q = np.eye(6) * 0.01  # Process noise
            kf.R = np.eye(3) * 0.1   # Measurement noise
            kf.P = np.eye(6) * 0.1   # Covariance
            filters[i] = kf
        return filters
        
    def update(self, landmarks):
        """Process new hand landmarks with precision tracking"""
        if landmarks is None:
            return None
            
        # Keep history for smoothing
        self.landmark_history.append(landmarks)
        if len(self.landmark_history) > self.history_max:
            self.landmark_history.pop(0)
            
        # Apply Kalman filtering to fingertips
        filtered_landmarks = landmarks.copy()
        for i in [4, 8, 12, 16, 20]:  # Filter fingertips for precision
            pos = np.array([landmarks[i][0], landmarks[i][1], landmarks[i][2]])
            
            # Update Kalman filter
            self.filters[i].predict()
            self.filters[i].update(pos)
            
            # Get filtered position
            filtered_pos = self.filters[i].x[:3]
            filtered_landmarks[i] = [filtered_pos[0], filtered_pos[1], filtered_pos[2]]
            
        # Calculate velocities if we have previous data
        velocities = {}
        if self.prev_landmarks is not None:
            for i in [4, 8, 12, 16, 20]:
                curr = np.array(filtered_landmarks[i])
                prev = np.array(self.prev_landmarks[i])
                velocities[i] = curr - prev
        
        self.prev_landmarks = filtered_landmarks
        
        return {
            "landmarks": filtered_landmarks,
            "velocities": velocities,
            "stable_palm": self._get_stable_palm(filtered_landmarks),
            "hand_orientation": self._calculate_hand_orientation(filtered_landmarks)
        }
        
    def _get_stable_palm(self, landmarks):
        """Calculate stable palm center for reference point"""
        # Use wrist and base of fingers (less movement than fingertips)
        palm_points = [0, 1, 5, 9, 13, 17]  # Wrist and finger bases
        palm_center = np.mean([landmarks[i] for i in palm_points], axis=0)
        return palm_center
        
    def _calculate_hand_orientation(self, landmarks):
        """Calculate 3D orientation of the hand"""
        try:
            # Create vectors from wrist to middle finger base and pinky base
            wrist = np.array(landmarks[0])
            middle_base = np.array(landmarks[9])
            pinky_base = np.array(landmarks[17])
            
            # Create two vectors to define the hand plane
            v1 = middle_base - wrist  # Points "up" from wrist
            v2 = pinky_base - wrist   # Points to side of hand
            
            # Normalize vectors (safely)
            v1_norm = np.linalg.norm(v1)
            v2_norm = np.linalg.norm(v2)
            
            if v1_norm > 0 and v2_norm > 0:
                v1 = v1 / v1_norm
                v2 = v2 / v2_norm
                
                # Get normal to hand plane
                normal = np.cross(v1, v2)
                normal_norm = np.linalg.norm(normal)
                
                if normal_norm > 0:
                    normal = normal / normal_norm
                    
                    # Create rotation matrix from these vectors
                    rotation_matrix = np.column_stack((v1, np.cross(normal, v1), normal))
                    
                    # Convert to quaternion for easier manipulation
                    r = Rotation.from_matrix(rotation_matrix)
                    return r.as_quat()
            
            # Fallback if any issues
            return np.array([0, 0, 0, 1])  # Identity quaternion
        except:
            # Safety fallback
            return np.array([0, 0, 0, 1]) 
        
    def detect_precise_gestures(self, data):
        """Detect precise gestures for CAD operations"""
        if not data:
            return {}
            
        landmarks = data["landmarks"]
        velocities = data.get("velocities", {})
        
        gestures = {}
        
        # Precision point (index finger pointing with minimal movement)
        if self._is_index_precision_pointing(landmarks, velocities):
            gestures["precision_point"] = {
                "confidence": 0.9,
                "position": landmarks[8],  # Index fingertip
                "direction": self._get_pointing_direction(landmarks)
            }
            
        # Pinch gesture (thumb and index together)
        pinch_degree = self._measure_pinch(landmarks)
        if pinch_degree < 0.05:  # Close pinch
            gestures["pinch"] = {
                "confidence": 0.9,
                "position": (np.array(landmarks[4]) + np.array(landmarks[8])) / 2,  # Between thumb and index
                "strength": 1.0 - pinch_degree * 20  # 0-1 strength based on closeness
            }
            
        # Measure finger spreading for scaling
        spread = self._measure_finger_spread(landmarks)
        gestures["spread_scale"] = {
            "confidence": 0.7 if spread > 0.3 else 0.0,
            "scale_factor": spread * 3  # Amplify for easier detection
        }
        
        # Three-finger system for fine controls
        if self._is_three_finger_control(landmarks):
            gestures["three_finger_control"] = {
                "confidence": 0.8,
                "position": landmarks[12],  # Middle fingertip
                "direction": self._get_middle_direction(landmarks)
            }
            
        # CAD Tool selection gestures
        tool_gesture = self.detect_tool_selection_gesture(landmarks)
        if tool_gesture:
            gestures["tool_selection"] = tool_gesture
            
        return gestures
        
    def detect_tool_selection_gesture(self, landmarks):
        """Detect gestures specifically for tool selection"""
        # Count extended fingers
        thumb_extended = self.is_thumb_extended(landmarks)
        index_extended = landmarks[8][1] < landmarks[5][1]
        middle_extended = landmarks[12][1] < landmarks[9][1]
        ring_extended = landmarks[16][1] < landmarks[13][1]
        pinky_extended = landmarks[20][1] < landmarks[17][1]
        
        extended_count = sum([index_extended, middle_extended, ring_extended, pinky_extended])
        
        # One finger up (index): Select tool
        if index_extended and not middle_extended and not ring_extended and not pinky_extended:
            return {"tool": "select", "confidence": 0.9}
            
        # Two fingers up (index + middle): Create tool
        elif index_extended and middle_extended and not ring_extended and not pinky_extended:
            return {"tool": "create", "confidence": 0.9}
            
        # Three fingers up (index + middle + ring): Move tool
        elif index_extended and middle_extended and ring_extended and not pinky_extended:
            return {"tool": "move", "confidence": 0.9}
            
        # Four fingers up (all except thumb): Scale tool
        elif index_extended and middle_extended and ring_extended and pinky_extended:
            return {"tool": "scale", "confidence": 0.9}
            
        # Thumb + index + pinky (phone gesture): Rotate tool
        elif thumb_extended and index_extended and not middle_extended and not ring_extended and pinky_extended:
            return {"tool": "rotate", "confidence": 0.9}
            
        # Rock sign (index + pinky): Extrude tool
        elif index_extended and not middle_extended and not ring_extended and pinky_extended and not thumb_extended:
            return {"tool": "extrude", "confidence": 0.9}
            
        return None
        
    def is_thumb_extended(self, landmarks):
        """Special function to detect if thumb is extended"""
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        thumb_mcp = landmarks[2]
        wrist = landmarks[0]
        
        # Calculate vectors
        wrist_to_mcp = np.array([thumb_mcp[0] - wrist[0], thumb_mcp[1] - wrist[1]])
        mcp_to_tip = np.array([thumb_tip[0] - thumb_mcp[0], thumb_tip[1] - thumb_mcp[1]])
        
        try:
            # Normalize vectors
            if np.linalg.norm(wrist_to_mcp) > 0 and np.linalg.norm(mcp_to_tip) > 0:
                wrist_to_mcp = wrist_to_mcp / np.linalg.norm(wrist_to_mcp)
                mcp_to_tip = mcp_to_tip / np.linalg.norm(mcp_to_tip)
                
                # Dot product tells us alignment
                dot_product = np.dot(wrist_to_mcp, mcp_to_tip)
                
                # If thumb is extended, vectors will be roughly aligned
                return dot_product > 0.7  # Threshold for thumb extension
        except:
            pass
            
        # Default if calculation fails
        return False
        
    def _is_index_precision_pointing(self, landmarks, velocities):
        """Detect precise pointing with index finger"""
        # Check if index is extended but others are closed
        index_extended = landmarks[8][1] < landmarks[5][1]  # Y position comparison
        middle_closed = not (landmarks[12][1] < landmarks[9][1])
        ring_closed = not (landmarks[16][1] < landmarks[13][1])
        pinky_closed = not (landmarks[20][1] < landmarks[17][1])
        
        pointing = index_extended and middle_closed and ring_closed and pinky_closed
        
        # Check if finger is stable (low velocity)
        stable = False
        if 8 in velocities:
            velocity_magnitude = np.linalg.norm(velocities[8])
            stable = velocity_magnitude < 0.01  # Low movement
            
        return pointing and stable
        
    def _get_pointing_direction(self, landmarks):
        """Get direction vector of pointing finger"""
        try:
            index_tip = np.array(landmarks[8])
            index_pip = np.array(landmarks[6])
            direction = index_tip - index_pip
            
            mag = np.linalg.norm(direction)
            if mag > 0:
                return direction / mag
        except:
            pass
            
        # Default fallback
        return np.array([0, 0, 1])
        
    def _get_middle_direction(self, landmarks):
        """Get direction vector of middle finger"""
        try:
            middle_tip = np.array(landmarks[12])
            middle_pip = np.array(landmarks[10])
            direction = middle_tip - middle_pip
            
            mag = np.linalg.norm(direction)
            if mag > 0:
                return direction / mag
        except:
            pass
            
        # Default fallback
        return np.array([0, 0, 1])
        
    def _measure_pinch(self, landmarks):
        """Measure distance between thumb and index finger tips"""
        thumb_tip = np.array(landmarks[4])
        index_tip = np.array(landmarks[8])
        distance = np.linalg.norm(thumb_tip - index_tip)
        return distance
        
    def _measure_finger_spread(self, landmarks):
        """Measure how spread out the fingers are (for scaling)"""
        tips = [8, 12, 16, 20]  # Index, middle, ring, pinky tips
        tip_positions = [np.array(landmarks[i]) for i in tips]
        
        # Calculate average distance between adjacent fingertips
        distances = []
        for i in range(len(tip_positions)-1):
            distances.append(np.linalg.norm(tip_positions[i] - tip_positions[i+1]))
        
        if distances:
            return np.mean(distances)
        return 0
        
    def _is_three_finger_control(self, landmarks):
        """Detect three fingers extended for precision control"""
        index_extended = landmarks[8][1] < landmarks[5][1]
        middle_extended = landmarks[12][1] < landmarks[9][1]
        ring_extended = landmarks[16][1] < landmarks[13][1]
        pinky_closed = not (landmarks[20][1] < landmarks[17][1])
        
        return index_extended and middle_extended and ring_extended and pinky_closed