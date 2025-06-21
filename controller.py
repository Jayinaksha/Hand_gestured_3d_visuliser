#!/usr/bin/env python3
"""
Iron Man Hand Gesture 3D Controller - Main Controller
Integrates all components for a complete hand gesture CAD system
"""

import cv2
import mediapipe as mp
import threading
import time
import random
import math
import pygame
import numpy as np
from ursina import *

from precision_tracking import PrecisionHandTracker
from gesture_system import GestureSystem
from cad_system import CADSystem
from ui_manager import UIManager

class IronManController:
    def __init__(self):
        # Control variables
        self.current_gesture = "none"
        self.last_action_time = 0
        self.action_cooldown = 0.8  # Prevent spam
        self.is_running = True
        self.debug_mode = True  # Set to True to see advanced hand tracking info
        
        # Hand position for camera control
        self.hand_position = None
        self.camera_control_active = False
        
        # Initialize component systems
        self.ui_manager = UIManager()
        
        # Initialize components
        self.setup_hand_tracking()
        self.setup_3d_world()
        self.setup_audio()
        
        # Initialize CAD system after 3D world is set up
        self.cad_system = CADSystem(self)
        
        # Add the precision tracker and gesture system
        self.precision_tracker = PrecisionHandTracker()
        self.gesture_system = GestureSystem()
        
        # Mode toggle detection
        self.mode_toggle_cooldown = 0
        self.mode_toggle_cooldown_time = 2.0  # seconds

        self.start_in_cad_mode = True
    
        # For simpler mode toggle
        self.mode_toggle_cooldown = 0
        self.mode_toggle_cooldown_time = 1.0  
        
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
        
        # Set up UI
        self.ui_elements = self.ui_manager.setup_ui()
        self.gesture_display = self.ui_elements["gesture_display"]
        self.action_display = self.ui_elements["action_display"]
        
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
            elif sound_type == "select":
                duration = 0.1
                frequency = 1200
            elif sound_type == "toggle":
                duration = 0.15
                frequency = 900
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
    
    def execute_gesture_action(self, gesture):
        """Execute actions based on gesture in normal mode"""
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
        drone.original_color = color.red
        
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
        
        chosen_color = random.choice(colors)
        box = Entity(
            model='cube',
            color=chosen_color,
            scale=random.uniform(0.4, 1.0),
            position=pos
        )
        box.original_color = chosen_color
        
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
                
        # Update CAD mode hover highlight if active
        if self.cad_system.active and self.cad_system.current_tool == "select":
            self.cad_system.update_hover_highlight(self.objects + self.drones)
    
    def check_for_mode_toggle(self, landmarks):
        """Check for gesture to toggle between normal and CAD mode"""
        # We'll use a specific gesture: All fingers up + thumbs up held for a moment
        thumb_extended = self.gesture_system.is_thumb_extended(landmarks)
        
        # Check if all fingers are extended
        index_extended = landmarks[8][1] < landmarks[5][1]
        middle_extended = landmarks[12][1] < landmarks[9][1]
        ring_extended = landmarks[16][1] < landmarks[13][1]
        pinky_extended = landmarks[20][1] < landmarks[17][1]
        
        all_extended = thumb_extended and index_extended and middle_extended and ring_extended and pinky_extended
        
        if all_extended:
            # If we're already timing a toggle, check if we've held long enough
            if self.mode_toggle_cooldown > 0:
                self.mode_toggle_cooldown -= time.dt
                
                if self.mode_toggle_cooldown <= 0:
                    # Toggle mode
                    self.toggle_cad_mode()
                    # Reset cooldown with negative value (prevents immediate re-toggle)
                    self.mode_toggle_cooldown = -self.mode_toggle_cooldown_time
            
            # If we're not in cooldown, start timing
            elif self.mode_toggle_cooldown == 0:
                self.mode_toggle_cooldown = self.mode_toggle_cooldown_time
                self.action_display.text = "HOLD TO SWITCH MODES..."
        else:
            # If gesture released and not in negative cooldown, reset
            if self.mode_toggle_cooldown > 0:
                self.mode_toggle_cooldown = 0
                
            # If in negative cooldown, count up
            elif self.mode_toggle_cooldown < 0:
                self.mode_toggle_cooldown = min(0, self.mode_toggle_cooldown + time.dt)
    
    def handle_cad_gestures(self, precision_data):
        """Process hand gestures for CAD mode"""
        if not precision_data:
            return
            
        # Detect precise gestures
        gestures = self.precision_tracker.detect_precise_gestures(precision_data)
        
        # Check for tool selection gesture
        if "tool_selection" in gestures:
            tool_data = gestures["tool_selection"]
            if tool_data["confidence"] > 0.8:
                self.cad_system.set_tool(tool_data["tool"])
                self.play_sound_effect("toggle")
        
        # Process gestures based on current tool
        if self.cad_system.current_tool == "select" and "precision_point" in gestures:
            point_data = gestures["precision_point"]
            if point_data["confidence"] > 0.8:
                world_pos = self.hand_to_world_position(point_data["position"])
                self.cad_system.select_object_at(world_pos)
                
        elif self.cad_system.current_tool == "create" and "precision_point" in gestures:
            point_data = gestures["precision_point"]
            if point_data["confidence"] > 0.8:
                world_pos = self.hand_to_world_position(point_data["position"])
                self.cad_system.place_object_at(world_pos)
                
        elif self.cad_system.current_tool == "move" and "pinch" in gestures:
            pinch_data = gestures["pinch"]
            if pinch_data["confidence"] > 0.8:
                world_pos = self.hand_to_world_position(pinch_data["position"])
                self.cad_system.move_selected_objects(world_pos)
                
        elif self.cad_system.current_tool == "scale" and "spread_scale" in gestures:
            scale_data = gestures["spread_scale"]
            if scale_data["confidence"] > 0.5:
                self.cad_system.scale_selected_objects(scale_data["scale_factor"])
                
        elif self.cad_system.current_tool == "rotate" and "three_finger_control" in gestures:
            control_data = gestures["three_finger_control"]
            if control_data["confidence"] > 0.7:
                self.cad_system.rotate_selected_objects(control_data)
                
        elif self.cad_system.current_tool == "extrude" and "pinch" in gestures:
            pinch_data = gestures["pinch"]
            if pinch_data["confidence"] > 0.8:
                world_pos = self.hand_to_world_position(pinch_data["position"])
                self.cad_system.extrude_selected_faces(world_pos, pinch_data["strength"])
                
        return gestures
                
    def hand_to_world_position(self, hand_pos):
        """Convert normalized hand position to world position"""
        # Map [0,1] hand space to world space
        x = (hand_pos[0] - 0.5) * 20  # Map [0,1] to [-10,10]
        y = (0.5 - hand_pos[1]) * 15  # Map [0,1] to [7.5,-7.5] (inverted y)
        z = hand_pos[2] * 10          # Map depth to [0,10]
        
        return Vec3(x, y, z)
    
    def toggle_cad_mode(self):
        """Switch between normal and CAD modes"""
        self.cad_system.toggle_active()
        
        if self.cad_system.active:
            self.ui_manager.update_ui_for_mode("cad")
            self.action_display.text = "CAD MODE ACTIVATED"
        else:
            self.ui_manager.update_ui_for_mode("normal")
            self.action_display.text = "NORMAL MODE ACTIVATED"
            
        self.play_sound_effect("toggle")

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
                    
                    # Check for mode toggle gesture
                    self.check_for_mode_toggle(landmarks)
                    
                    # Process with precision tracker if in CAD mode
                    if self.cad_system.active:
                        precision_data = self.precision_tracker.update(landmarks)
                        
                        # Handle CAD-specific gestures
                        cad_gestures = self.handle_cad_gestures(precision_data)
                        
                        # Visualize precision tracking if in debug mode
                        if self.debug_mode and precision_data:
                            self.ui_manager.visualize_precision_tracking(frame, precision_data, cad_gestures or {})
                            
                        # Draw CAD tool selector
                        self.ui_manager.draw_cad_tool_selector(frame, self.cad_system.current_tool, h, w)
                    else:
                        # Detect standard gesture for normal mode
                        gesture = self.gesture_system.detect_gesture(landmarks, hand_idx)
                        
                        # Only update from first hand to prevent conflicts
                        if hand_idx == 0:
                            self.current_gesture = gesture
                        
                            # Update display with gesture name
                            display_name = self.gesture_system.get_gesture_name(gesture)
                            if self.gesture_display:
                                self.gesture_display.text = f"{display_name}"
                            
                            # Execute action for normal mode
                            self.execute_gesture_action(gesture)
                        
                        # Camera control with open palm in normal mode
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
                        if self.debug_mode and hasattr(self.gesture_system, 'gesture_confidence'):
                            self.ui_manager.draw_confidence_bars(frame, self.gesture_system.gesture_confidence)
            
            # Display camera feed with improved UI
            # Add semi-transparent overlay for better text visibility
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, 60), (0, 0, 0), -1)
            cv2.rectangle(overlay, (0, h-40), (w, h), (0, 0, 0), -1)
            frame = cv2.addWeighted(overlay, 0.3, frame, 0.7, 0)
            
            # Show different header based on mode
            header_text = "IRON MAN CAD SYSTEM" if self.cad_system.active else "IRON MAN INTERFACE"
            cv2.putText(frame, header_text, 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                       
            # Show current info in status bar
            if self.cad_system.active:
                cv2.putText(frame, f"Tool: {self.cad_system.current_tool.upper()} | Type: {self.cad_system.primitive_type.upper()}", 
                           (10, h-15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
            else:
                cv2.putText(frame, f"Current: {self.current_gesture}", 
                           (10, h-15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            # Actually show the camera frame
            cv2.imshow('Iron Man CAD System (Press Q to exit)', frame)
            
            if cv2.waitKey(5) & 0xFF == ord('q'):
                self.is_running = False
                break
        
        cap.release()
        cv2.destroyAllWindows()
        print("Camera control stopped!")

    def run(self):
        """Start the Iron Man interface"""
        print("=== IRON MAN GESTURE CAD SYSTEM ===")
        print("You are now Tony Stark!")
        print("Use hand gestures to control your 3D world!")
        print("Hold all fingers extended to toggle between modes")
        print("In CAD mode, use different finger gestures to select tools:")
        print("- 1 finger: Select tool")  
        print("- 2 fingers: Create tool")
        print("- 3 fingers: Move tool")
        print("- 4 fingers: Scale tool")
        print("- Rock sign: Extrude tool")
        print("- Phone gesture: Rotate tool")
        
        # Define update function for Ursina
        def update():
            self.update_world()
        
        # Activate CAD mode immediately if specified
        if self.start_in_cad_mode:
            self.toggle_cad_mode()
            print("Starting directly in CAD mode!")

        # Start camera control thread
        camera_thread = threading.Thread(target=self.camera_control_thread)
        camera_thread.daemon = True
        camera_thread.start()
        
        # Add some starting objects
        self.spawn_box()
        self.spawn_drone()
        
        print("3D World is running!")
        print("Press ESC in 3D world or Q in camera window to exit")
        
        # Run the 3D world
        self.app.run()
        
        # When Ursina window closes
        self.is_running = False
        print("Shutting down...")