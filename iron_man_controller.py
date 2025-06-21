#!/usr/bin/env python3
"""
🔥🔥🔥 IRON MAN HAND GESTURE 3D CONTROLLER - ENHANCED! 🔥🔥🔥
The ultimate fusion of hand tracking + 3D world control!
"""

import cv2
import mediapipe as mp
import threading
import time
from ursina import *
import random
import math
import pygame
import numpy as np

class IronManController:
    def __init__(self):
        # Initialize components
        self.setup_hand_tracking()
        self.setup_3d_world()
        self.setup_audio()
        
        # Control variables
        self.current_gesture = "none"
        self.last_action_time = 0
        self.action_cooldown = 0.8  # Prevent spam
        self.is_running = True
        self.debug_mode = True  # Set to True to see advanced hand tracking info
        
        # Hand position for camera control
        self.hand_position = None
        self.camera_control_active = False
        
        # For gesture visualization
        self.gesture_confidence = {}
        
    def setup_hand_tracking(self):
        """Initialize hand tracking with improved settings"""
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.6,  # Lower threshold for better detection
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
    def setup_3d_world(self):
        """Initialize the 3D world"""
        self.app = Ursina()
        
        # Create the world
        self.ground = Entity(
            model='cube',
            color=color.dark_gray,
            scale=(25, 0.5, 25),
            position=(0, -2, 0)
        )
        
        # Sky and lighting
        sky = Sky()
        DirectionalLight().look_at(Vec3(1, -1, -1))
        
        # Camera setup
        camera.position = (0, 3, -8)
        camera.rotation_x = 10
        
        # Storage for objects
        self.objects = []
        self.drones = []
        self.bullets = []
        
        # UI - Using plain text instead of emojis
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
        
        # Add some initial objects for reference
        Entity(model='cube', color=color.orange, scale=0.8, position=(4, 0, 3))
        Entity(model='sphere', color=color.violet, scale=0.6, position=(-4, 0, 3))
        
    def setup_audio(self):
        """Initialize audio system"""
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.audio_enabled = True
        except:
            self.audio_enabled = False
            print("⚠️ Audio not available, but visuals will work!")
    
    def play_sound_effect(self, sound_type):
        """Play sound effects"""
        if not self.audio_enabled:
            return
        
        try:
            if sound_type == "spawn":
                duration = 0.2
                frequency = 600
            elif sound_type == "shoot":
                duration = 0.1
                frequency = 800
            elif sound_type == "drone":
                duration = 0.3
                frequency = 300
            elif sound_type == "explode":
                duration = 0.5
                frequency = 200
            else:
                return
                
            # Simple beep generation
            frames = int(duration * 22050)
            arr = []
            for i in range(frames):
                wave = math.sin(2 * math.pi * frequency * i / 22050) * 0.3
                arr.append([wave, wave])
            
            sound_array = np.array(arr, dtype=np.float32)
            sound = pygame.sndarray.make_sound((sound_array * 32767).astype(np.int16))
            sound.play()
        except Exception as e:
            print(f"Sound error: {e}")
    
    def detect_gesture(self, landmarks, hand_idx=0):
        """
        Improved hand gesture detection with better accuracy
        """
        if not landmarks:
            return "none"
        
        # Extract key points
        wrist = np.array([landmarks[0][0], landmarks[0][1]])
        thumb_tip = np.array([landmarks[4][0], landmarks[4][1]])
        thumb_mcp = np.array([landmarks[2][0], landmarks[2][1]])
        index_tip = np.array([landmarks[8][0], landmarks[8][1]])
        index_pip = np.array([landmarks[6][0], landmarks[6][1]])
        index_mcp = np.array([landmarks[5][0], landmarks[5][1]])
        middle_tip = np.array([landmarks[12][0], landmarks[12][1]])
        middle_pip = np.array([landmarks[10][0], landmarks[10][1]])
        ring_tip = np.array([landmarks[16][0], landmarks[16][1]])
        ring_pip = np.array([landmarks[14][0], landmarks[14][1]])
        pinky_tip = np.array([landmarks[20][0], landmarks[20][1]])
        pinky_pip = np.array([landmarks[18][0], landmarks[18][1]])
        
        # Calculate finger extension using improved vector approach
        # A finger is extended if tip is further from palm than pip
        def distance(p1, p2):
            return np.sqrt(np.sum((p1 - p2) ** 2))
        
        # Check if fingers are extended
        thumb_extended = self.is_thumb_extended(landmarks)
        index_extended = index_tip[1] < index_pip[1] 
        middle_extended = middle_tip[1] < middle_pip[1]
        ring_extended = ring_tip[1] < ring_pip[1]
        pinky_extended = pinky_tip[1] < pinky_pip[1]
        
        # Calculate pinch distance
        pinch_distance = distance(thumb_tip, index_tip)
        is_pinching = pinch_distance < 0.05  # Threshold for pinch detection
        
        # Store finger states
        finger_states = [thumb_extended, index_extended, middle_extended, ring_extended, pinky_extended]
        
        # Debug logging
        if self.debug_mode and hand_idx == 0:
            print(f"Finger states: {finger_states}, Pinch: {is_pinching:.3f}")
        
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
            
        # Update the gesture confidence history (for visualization)
        self.gesture_confidence = confidences
        
        # Return the gesture with highest confidence
        best_gesture = max(confidences.items(), key=lambda x: x[1])
        if best_gesture[1] > 0.5:  # Threshold for detection
            return best_gesture[0]
        
        return "unknown"
    
    def is_thumb_extended(self, landmarks):
        """
        Special function to detect thumb extension since it moves differently
        """
        thumb_tip = landmarks[4]
        thumb_mcp = landmarks[2] 
        wrist = landmarks[0]
        
        # Calculate vectors
        wrist_to_mcp = np.array([thumb_mcp[0] - wrist[0], thumb_mcp[1] - wrist[1]])
        mcp_to_tip = np.array([thumb_tip[0] - thumb_mcp[0], thumb_tip[1] - thumb_mcp[1]])
        
        # Normalize vectors
        wrist_to_mcp = wrist_to_mcp / np.linalg.norm(wrist_to_mcp)
        mcp_to_tip = mcp_to_tip / np.linalg.norm(mcp_to_tip)
        
        # Dot product tells us alignment
        dot_product = np.dot(wrist_to_mcp, mcp_to_tip)
        
        # If thumb is extended, vectors will be roughly aligned
        return dot_product > 0.7  # Threshold for thumb extension
    
    def execute_gesture_action(self, gesture):
        """Execute actions based on gesture"""
        current_time = time.time()
        
        # Check cooldown
        if current_time - self.last_action_time < self.action_cooldown and gesture != "open_palm":
            return
        
        if gesture == "fist":
            self.spawn_drone()
            self.action_display.text = "DRONE DEPLOYED!"
            self.play_sound_effect("drone")
            
        elif gesture == "peace":
            self.shoot_bullet()
            self.action_display.text = "BULLET FIRED!"
            self.play_sound_effect("shoot")
            
        elif gesture == "pinch":
            self.spawn_box()
            self.action_display.text = "BOX SPAWNED!"
            self.play_sound_effect("spawn")
            
        elif gesture == "thumbs_up":
            self.rotate_all_objects()
            self.action_display.text = "OBJECTS ROTATED!"
            
        elif gesture == "rock_sign":
            self.create_explosion()
            self.action_display.text = "EXPLOSION!"
            self.play_sound_effect("explode")
            
        elif gesture == "open_palm":
            self.action_display.text = "CAMERA CONTROL ACTIVE"
            self.camera_control_active = True
            return  # Don't update last_action_time for continuous control
        else:
            self.camera_control_active = False
        
        self.last_action_time = current_time
    
    def spawn_drone(self, pos=None):
        """Spawn a cool drone"""
        if pos is None:
            pos = (random.uniform(-6, 6), random.uniform(2, 5), random.uniform(-3, 8))
        
        # Main body
        drone = Entity(
            model='sphere',
            color=color.red,
            scale=0.8,
            position=pos
        )
        
        # Add glowing effect
        drone.always_on_top = False
        
        # Propellers
        for i in range(4):
            angle = i * 90
            prop_x = math.cos(math.radians(angle)) * 0.7
            prop_z = math.sin(math.radians(angle)) * 0.7
            
            Entity(
                model='cube',
                color=color.black,
                scale=(0.5, 0.05, 0.05),
                position=(pos[0] + prop_x, pos[1] + 0.2, pos[2] + prop_z)
            )
        
        self.drones.append(drone)
        print(f"Drone spawned at {pos}")
    
    def spawn_box(self, pos=None):
        """Spawn a colorful box"""
        if pos is None:
            pos = (random.uniform(-5, 5), 1, random.uniform(-2, 6))
        
        # List of available colors
        colors = [color.red, color.blue, color.green, color.yellow, 
                 color.orange, color.cyan, color.magenta, color.lime]
        
        box = Entity(
            model='cube',
            color=random.choice(colors),
            scale=random.uniform(0.4, 1.0),
            position=pos
        )
        
        self.objects.append(box)
        print(f"Box spawned at {pos}")
    
    def shoot_bullet(self):
        """Fire a bullet"""
        start_pos = Vec3(camera.position.x, camera.position.y, camera.position.z)
        
        bullet = Entity(
            model='sphere',
            color=color.yellow,
            scale=0.15,
            position=start_pos
        )
        
        # Give bullet velocity in camera direction
        bullet.velocity = camera.forward * 20
        self.bullets.append(bullet)
        print("Bullet fired!")
    
    def rotate_all_objects(self):
        """Rotate all spawned objects"""
        for obj in self.objects + self.drones:
            if obj:
                obj.rotation_y += random.uniform(30, 90)
        print("All objects rotated!")
    
    def create_explosion(self):
        """Create explosion effect"""
        explosion_colors = [color.red, color.orange, color.yellow, color.white]
        
        explosion_center = (
            random.uniform(-5, 5),
            random.uniform(0, 3),
            random.uniform(-3, 5)
        )
        
        for i in range(15):
            # Calculate random offset from center
            offset = (
                random.uniform(-2, 2),
                random.uniform(-1, 3),
                random.uniform(-2, 2)
            )
            
            position = (
                explosion_center[0] + offset[0],
                explosion_center[1] + offset[1],
                explosion_center[2] + offset[2]
            )
            
            explosion_bit = Entity(
                model='cube',
                color=random.choice(explosion_colors),
                scale=random.uniform(0.2, 0.8),
                position=position
            )
            
            # Make explosion bits disappear after 2 seconds
            destroy(explosion_bit, delay=2)
        
        print("EXPLOSION CREATED!")
    
    def update_world(self):
        """Update world physics"""
        # Move bullets
        for bullet in self.bullets[:]:
            if bullet and hasattr(bullet, 'velocity'):
                bullet.position += bullet.velocity * time.dt
                
                # Check collision with objects
                for obj in self.objects[:]:
                    if obj and distance(bullet.position, obj.position) < 1:
                        destroy(obj)
                        destroy(bullet)
                        self.objects.remove(obj)
                        self.bullets.remove(bullet)
                        print("HIT!")
                        break
                
                # Remove distant bullets
                if distance(bullet.position, Vec3(0, 0, 0)) > 50:
                    destroy(bullet)
                    self.bullets.remove(bullet)
        
        # Animate drones
        for drone in self.drones:
            if drone:
                drone.rotation_y += 120 * time.dt
                # Make drones hover
                drone.y += math.sin(time.time() * 2 + hash(drone) % 100) * 0.01
    
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
    
    def camera_control_thread(self):
        """Thread for camera and hand tracking"""
        # Make sure we're using the default camera (index 0)
        cap = cv2.VideoCapture(0)
        
        # Try to set reasonable resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        if not cap.isOpened():
            print("ERROR: Could not open camera!")
            return
        
        print("Camera control thread started!")
        
        while self.is_running:
            ret, frame = cap.read()
            if not ret:
                print("Failed to get frame from camera. Retrying...")
                time.sleep(0.5)
                continue
            
            frame = cv2.flip(frame, 1)  # Mirror image
            h, w, _ = frame.shape
            
            # Process hands
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)
            
            # Reset gesture if no hands detected
            if not results.multi_hand_landmarks:
                # Just gradually fade the UI displays
                curr_gesture = self.gesture_display.text
                if curr_gesture != "WAITING...":
                    self.gesture_display.text = "WAITING..."
                    self.camera_control_active = False
                    
            if results.multi_hand_landmarks:
                for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                    # Draw hand landmarks with better visibility
                    self.mp_drawing.draw_landmarks(
                        frame, 
                        hand_landmarks, 
                        self.mp_hands.HAND_CONNECTIONS,
                        self.mp_drawing_styles.get_default_hand_landmarks_style(),
                        self.mp_drawing_styles.get_default_hand_connections_style()
                    )
                    
                    # Get landmarks as array
                    landmarks = []
                    for lm in hand_landmarks.landmark:
                        landmarks.append([lm.x, lm.y, lm.z])
                    
                    # Detect gesture with improved algorithm
                    gesture = self.detect_gesture(landmarks, hand_idx)
                    
                    # Only update from first hand to prevent conflicts
                    if hand_idx == 0:
                        self.current_gesture = gesture
                    
                        # Update display - using plain text instead of emojis
                        gesture_names = {
                            "fist": "FIST",
                            "peace": "PEACE", 
                            "open_palm": "OPEN PALM",
                            "pinch": "PINCH",
                            "thumbs_up": "THUMBS UP",
                            "rock_sign": "ROCK SIGN"
                        }
                        
                        display_name = gesture_names.get(gesture, gesture.upper())
                        if self.gesture_display:
                            self.gesture_display.text = f"{display_name}"
                        
                        # Execute action
                        self.execute_gesture_action(gesture)
                    
                    # Camera control with open palm
                    if gesture == "open_palm" and hand_idx == 0 and self.camera_control_active:
                        index_tip = landmarks[8]
                        # Map hand position to camera movement
                        move_x = (index_tip[0] - 0.5) * 6  # Increased sensitivity
                        move_y = (index_tip[1] - 0.5) * 6
                        
                        try:
                            # Smooth camera movement
                            target_pos = Vec3(move_x, max(1, 3 - move_y), -8)
                            camera.position = lerp(camera.position, target_pos, time.dt * 1.5)
                        except Exception as e:
                            print(f"Camera control error: {e}")
            
            # Display gesture confidence bars in debug mode
            if self.debug_mode and self.gesture_confidence:
                self.draw_confidence_bars(frame, self.gesture_confidence)
            
            # Display camera feed with improved UI
            # Add semi-transparent overlay for better text visibility
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, 60), (0, 0, 0), -1)
            cv2.rectangle(overlay, (0, h-40), (w, h), (0, 0, 0), -1)
            frame = cv2.addWeighted(overlay, 0.3, frame, 0.7, 0)
            
            cv2.putText(frame, "IRON MAN INTERFACE", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            cv2.putText(frame, f"Current: {self.current_gesture}", 
                       (10, h-15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            # Actually show the camera frame
            cv2.imshow('Iron Man Hand Control (Press Q to exit)', frame)
            
            if cv2.waitKey(5) & 0xFF == ord('q'):
                self.is_running = False
                break
        
        cap.release()
        cv2.destroyAllWindows()
        print("Camera control stopped!")
    
    def run(self):
        """Start the Iron Man interface"""
        print("IRON MAN INTERFACE ACTIVATED!")
        print("You are now Tony Stark!")
        print("Use hand gestures to control your 3D world!")
        print("Camera window will open for gesture control")
        print("Use WASD + mouse in 3D world for additional control")
        
        # Start camera control thread
        camera_thread = threading.Thread(target=self.camera_control_thread)
        camera_thread.daemon = True
        camera_thread.start()
        
        # World update function
        def update():
            self.update_world()
        
        # Add some starting objects - FIXED by not passing position parameters initially
        self.spawn_box()
        self.spawn_drone()
        
        print("3D World is running!")
        print("Press ESC in 3D world to exit")
        
        # Register the world update function
        self.app.run()
        
        # When Ursina window closes
        self.is_running = False

if __name__ == "__main__":
    controller = IronManController()
    controller.run()