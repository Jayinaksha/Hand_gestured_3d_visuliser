#!/usr/bin/env python3
"""
UI Manager Module
Handles all UI-related functionality
"""

import cv2
import numpy as np
from ursina import *

class UIManager:
    def __init__(self):
        # UI state tracking
        self.current_mode = "normal"  # normal or cad
        
    def setup_ui(self):
        """Set up UI elements for both modes"""
        # Main UI elements
        self.gesture_display = Text(
            'IRON MAN READY',
            position=(-0.85, 0.45),
            scale=1.8,
            color=color.cyan
        )
        
        self.action_display = Text(
            'Waiting for gesture...',
            position=(-0.85, 0.35),
            scale=1.2,
            color=color.yellow
        )
        
        self.controls = Text(
            'FIST - Drone | PEACE - Shoot | PALM - Camera\nPINCH - Box | THUMBS - Rotate | ROCK - Explode',
            position=(-0.85, -0.4),
            scale=1,
            color=color.white
        )
        
        # Mode switch help
        self.mode_help = Text(
            'HOLD ALL FINGERS UP TO TOGGLE CAD MODE',
            position=(-0.85, -0.45),
            scale=0.7,
            color=color.light_gray
        )
        
        return {
            "gesture_display": self.gesture_display,
            "action_display": self.action_display,
            "controls": self.controls,
            "mode_help": self.mode_help
        }
        
    def update_ui_for_mode(self, mode):
        """Update UI elements based on current mode"""
        self.current_mode = mode
        
        if mode == "normal":
            self.controls.visible = True
            self.gesture_display.text = "IRON MAN READY"
        else:
            self.controls.visible = False
            self.gesture_display.text = "CAD MODE ACTIVE"
    
    def draw_confidence_bars(self, frame, confidences, pos=(20, 300), width=100, height=15, gap=20):
        """Draw confidence bars for each gesture"""
        gestures = ["fist", "thumbs_up", "peace", "open_palm", "pinch", "rock_sign"]
        
        for i, gesture in enumerate(gestures):
            conf = confidences.get(gesture, 0)
            y_pos = pos[1] + i * gap
            
            # Draw gesture name
            cv2.putText(frame, f"{gesture}", (pos[0] - 100, y_pos + 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            
            # Draw background bar
            cv2.rectangle(frame, (pos[0], y_pos), (pos[0] + width, y_pos + height), 
                          (50, 50, 50), -1)
            
            # Draw confidence bar
            bar_width = int(conf * width)
            color = (0, 255, 0) if conf > 0.5 else (0, 165, 255)
            cv2.rectangle(frame, (pos[0], y_pos), (pos[0] + bar_width, y_pos + height), 
                          color, -1)
            
            # Draw percentage
            cv2.putText(frame, f"{int(conf * 100)}%", (pos[0] + width + 10, y_pos + 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
                        
    def draw_cad_tool_selector(self, frame, current_tool, h, w):
        """Draw CAD tool selection guide in camera window"""
        # Draw tool indicator at bottom
        tools = ["select", "create", "move", "scale", "rotate", "extrude"]
        
        tool_width = w // len(tools)
        for i, tool in enumerate(tools):
            x1 = i * tool_width
            x2 = (i+1) * tool_width
            
            # Background
            color = (0, 120, 0) if tool == current_tool else (60, 60, 60)
            cv2.rectangle(frame, (x1, h-70), (x2, h-30), color, -1)
            
            # Tool name
            cv2.putText(frame, tool.upper(), (x1 + 5, h-45),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                        
        # Draw gesture guide
        cv2.putText(frame, "GESTURE TOOL SELECTION:", (10, h-85),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        cv2.putText(frame, "1 FINGER: SELECT | 2 FINGERS: CREATE | 3 FINGERS: MOVE", (10, h-105),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1) 
        cv2.putText(frame, "4 FINGERS: SCALE | ROCK SIGN: EXTRUDE | PHONE: ROTATE", (10, h-125),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
                    
    def visualize_precision_tracking(self, frame, precision_data, gestures):
        """Visualize precision tracking data on the camera frame"""
        if not precision_data:
            return
            
        h, w, _ = frame.shape
        landmarks = precision_data["landmarks"]
        
        # Draw filtered fingertips
        for i in [4, 8, 12, 16, 20]:  # Thumb, index, middle, ring, pinky tips
            x, y = int(landmarks[i][0] * w), int(landmarks[i][1] * h)
            cv2.circle(frame, (x, y), 8, (0, 255, 0), -1)
            
        # Draw pointing direction if available
        try:
            if "precision_point" in gestures:
                point_data = gestures["precision_point"]
                if point_data["confidence"] > 0.8:
                    pos = point_data["position"]
                    direction = point_data["direction"]
                    
                    # Make sure we get scalar values
                    pos_x = float(pos[0]) if isinstance(pos[0], np.ndarray) else float(pos[0])
                    pos_y = float(pos[1]) if isinstance(pos[1], np.ndarray) else float(pos[1])
                    
                    dir_x = float(direction[0]) if isinstance(direction[0], np.ndarray) else float(direction[0])
                    dir_y = float(direction[1]) if isinstance(direction[1], np.ndarray) else float(direction[1])
                    
                    # Calculate endpoint for drawing the direction arrow
                    start_x = int(pos_x * w)
                    start_y = int(pos_y * h)
                    end_x = int((pos_x + dir_x * 0.2) * w)
                    end_y = int((pos_y + dir_y * 0.2) * h)
                    
                    # Draw arrow if points are valid
                    if 0 <= start_x < w and 0 <= start_y < h and 0 <= end_x < w and 0 <= end_y < h:
                        cv2.arrowedLine(frame, (start_x, start_y), (end_x, end_y), 
                                       (0, 0, 255), 3)
        except Exception as e:
            # Safe error handling - just skip drawing if there's an issue
            print(f"Visualization error (non-critical): {e}")
                
        # Draw palm center
        try:
            palm = precision_data["stable_palm"]
            palm_x = int(float(palm[0]) * w)
            palm_y = int(float(palm[1]) * h)
            cv2.circle(frame, (palm_x, palm_y), 12, (255, 0, 0), 2)
        except:
            pass
        
        # Draw tool selection gesture indicator if available
        if "tool_selection" in gestures:
            tool_gesture = gestures["tool_selection"]
            tool_name = tool_gesture["tool"]
            confidence = tool_gesture["confidence"]
            
            cv2.putText(frame, f"TOOL: {tool_name.upper()} ({int(confidence*100)}%)", 
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)