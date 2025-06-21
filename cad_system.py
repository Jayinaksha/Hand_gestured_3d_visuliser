#!/usr/bin/env python3
"""
CAD System Module
Handles CAD-specific operations and tools
"""

from ursina import *
import random
import numpy as np
import time

class CADSystem:
    def __init__(self, parent_controller):
        self.controller = parent_controller
        
        # CAD state
        self.active = False
        self.current_tool = "select"
        self.primitive_type = "box"
        self.selected_objects = []
        self.hover_object = None
        
        # Grid settings
        self.grid_visible = False
        self.grid_size = 0.5
        self.snap_to_grid = True
        self.grid_entities = []
        
        # Tool last used timestamps (for cooldown)
        self.last_tool_use = {}
        self.tool_cooldown = 1.0  # seconds
        
        # Create grid
        self.create_grid()
        
        # Create CAD-specific UI
        self.setup_ui()
        
    def create_grid(self):
        """Create a reference grid for CAD mode"""
        grid_size = 10
        
        # Create horizontal grid lines
        for i in range(-grid_size, grid_size + 1):
            line = Entity(
                model=Mesh(vertices=[(-grid_size, 0, i * self.grid_size), (grid_size, 0, i * self.grid_size)], 
                           mode='line'),
                color=color.gray if i != 0 else color.blue,
                position=(0, 0, 0)
            )
            self.grid_entities.append(line)
            line.visible = False
            
        # Create vertical grid lines
        for i in range(-grid_size, grid_size + 1):
            line = Entity(
                model=Mesh(vertices=[(i * self.grid_size, 0, -grid_size), (i * self.grid_size, 0, grid_size)], 
                           mode='line'),
                color=color.gray if i != 0 else color.red,
                position=(0, 0, 0)
            )
            self.grid_entities.append(line)
            line.visible = False
            
    def setup_ui(self):
        """Create UI elements for CAD mode"""
        self.tool_display = Text(
            'CAD MODE: OFF',
            position=(-0.85, 0.25),
            scale=1.0,
            color=color.lime
        )
        self.tool_display.visible = False
        
        self.primitive_display = Text(
            'PRIMITIVE: BOX',
            position=(-0.85, 0.15),
            scale=0.8,
            color=color.lime
        )
        self.primitive_display.visible = False
        
        self.help_text = Text(
            'GESTURE CONTROLS:\n'
            '1 FINGER - Select | 2 FINGERS - Create | 3 FINGERS - Move\n'
            '4 FINGERS - Scale | THUMB+INDEX+PINKY - Rotate | ROCK - Extrude',
            position=(-0.85, -0.35),
            scale=0.7,
            color=color.light_gray
        )
        self.help_text.visible = False
        
    def toggle_active(self):
        """Toggle CAD mode on/off"""
        self.active = not self.active
        
        if self.active:
            # Show UI elements
            self.tool_display.visible = True
            self.primitive_display.visible = True
            self.help_text.visible = True
            
            # Update tool display
            self.set_tool("select")
            
            # Show grid
            self.toggle_grid_visibility(True)
        else:
            # Hide UI elements
            self.tool_display.visible = False
            self.primitive_display.visible = False
            self.help_text.visible = False
            
            # Hide grid
            self.toggle_grid_visibility(False)
            
            # Clear selection
            self.clear_selection()
            
    def toggle_grid_visibility(self, state=None):
        """Toggle grid visibility"""
        if state is not None:
            self.grid_visible = state
        else:
            self.grid_visible = not self.grid_visible
            
        for entity in self.grid_entities:
            entity.visible = self.grid_visible
            
    def set_tool(self, tool_name):
        """Set the current CAD tool"""
        self.current_tool = tool_name
        self.tool_display.text = f'CAD TOOL: {tool_name.upper()}'
        
    def cycle_primitive(self):
        """Cycle through primitive types"""
        primitives = ["box", "sphere", "cylinder", "pyramid"]
        current_index = primitives.index(self.primitive_type) if self.primitive_type in primitives else 0
        self.primitive_type = primitives[(current_index + 1) % len(primitives)]
        self.primitive_display.text = f'PRIMITIVE: {self.primitive_type.upper()}'
        
    def can_use_tool(self, tool_name):
        """Check if tool can be used (cooldown timer)"""
        now = time.time()
        if tool_name not in self.last_tool_use:
            self.last_tool_use[tool_name] = 0
            
        if now - self.last_tool_use[tool_name] > self.tool_cooldown:
            self.last_tool_use[tool_name] = now
            return True
            
        return False
        
    def clear_selection(self):
        """Clear currently selected objects"""
        for obj in self.selected_objects:
            if hasattr(obj, 'original_color'):
                obj.color = obj.original_color
                
        self.selected_objects = []
        
    def select_object_at(self, position, radius=0.5):
        """Select object near position"""
        # Don't select if tool was used recently
        if not self.can_use_tool("select"):
            return
            
        closest_obj = None
        closest_distance = float('inf')
        
        # Find closest object to position
        all_objects = self.controller.objects + self.controller.drones
        for obj in all_objects:
            if obj:
                dist = distance(position, obj.position)
                if dist < closest_distance and dist < radius:
                    closest_distance = dist
                    closest_obj = obj
        
        # Handle selection
        if closest_obj:
            if closest_obj in self.selected_objects:
                # Deselect if already selected
                self.selected_objects.remove(closest_obj)
                closest_obj.color = closest_obj.original_color if hasattr(closest_obj, 'original_color') else color.white
                self.controller.action_display.text = "OBJECT DESELECTED"
            else:
                # Select object
                if not hasattr(closest_obj, 'original_color'):
                    closest_obj.original_color = closest_obj.color
                
                self.selected_objects.append(closest_obj)
                closest_obj.color = color.yellow  # Highlight color
                self.controller.action_display.text = "OBJECT SELECTED"
                
            self.controller.play_sound_effect("select")
        else:
            # If clicking empty space, clear selection
            for obj in self.selected_objects:
                if hasattr(obj, 'original_color'):
                    obj.color = obj.original_color
                    
            self.selected_objects = []
            if all_objects:  # Only update text if there are objects
                self.controller.action_display.text = "SELECTION CLEARED"
    
    def place_object_at(self, position):
        """Place new object at position"""
        # Don't create if tool was used recently
        if not self.can_use_tool("create"):
            return
            
        # Snap to grid if enabled
        if self.snap_to_grid:
            position = self.snap_position_to_grid(position)
            
        # Create object based on current primitive type
        if self.primitive_type == "box":
            obj = Entity(
                model='cube',
                color=color.white,
                scale=(1, 1, 1),
                position=position
            )
            obj.original_color = color.white
            self.controller.objects.append(obj)
            self.controller.action_display.text = "BOX CREATED"
            
        elif self.primitive_type == "sphere":
            obj = Entity(
                model='sphere',
                color=color.white,
                scale=(1, 1, 1),
                position=position
            )
            obj.original_color = color.white
            self.controller.objects.append(obj)
            self.controller.action_display.text = "SPHERE CREATED"
            
        elif self.primitive_type == "cylinder":
            obj = Entity(
                model='cylinder',
                color=color.white,
                scale=(1, 1, 1),
                position=position
            )
            obj.original_color = color.white
            self.controller.objects.append(obj)
            self.controller.action_display.text = "CYLINDER CREATED"
            
        elif self.primitive_type == "pyramid":
            obj = Entity(
                model='cone',
                color=color.white,
                scale=(1, 1, 1),
                position=position
            )
            obj.original_color = color.white
            self.controller.objects.append(obj)
            self.controller.action_display.text = "PYRAMID CREATED"
            
        self.controller.play_sound_effect("spawn")
    
    def move_selected_objects(self, position):
        """Move selected objects to position"""
        if not self.selected_objects:
            return
            
        # Snap to grid if enabled
        if self.snap_to_grid:
            position = self.snap_position_to_grid(position)
            
        # Calculate center of selected objects
        center = Vec3(0, 0, 0)
        for obj in self.selected_objects:
            center += obj.position
        center /= len(self.selected_objects)
        
        # Calculate offset
        offset = position - center
        
        # Apply movement to all selected objects
        for obj in self.selected_objects:
            obj.position = lerp(obj.position, obj.position + offset, time.dt * 5)
            
    def snap_position_to_grid(self, position):
        """Snap a position to the nearest grid point"""
        return Vec3(
            round(position.x / self.grid_size) * self.grid_size,
            round(position.y / self.grid_size) * self.grid_size, 
            round(position.z / self.grid_size) * self.grid_size
        )
    
    def scale_selected_objects(self, scale_factor):
        """Scale selected objects"""
        if not self.selected_objects:
            return
            
        for obj in self.selected_objects:
            # Apply scale gradually
            target_scale = obj.scale * (1 + (scale_factor - 1) * time.dt * 2)
            
            # Limit scale to reasonable bounds
            max_scale = 5
            min_scale = 0.1
            
            # Apply limits
            target_scale.x = max(min_scale, min(max_scale, target_scale.x))
            target_scale.y = max(min_scale, min(max_scale, target_scale.y))
            target_scale.z = max(min_scale, min(max_scale, target_scale.z))
            
            obj.scale = target_scale
            
    def rotate_selected_objects(self, control_data):
        """Rotate selected objects based on hand movement"""
        if not self.selected_objects:
            return
            
        position = control_data["position"]
        direction = control_data["direction"]
        
        # Calculate rotation amount based on hand position
        rotation_y = (position[0] - 0.5) * 5  # Map x-position to rotation
        
        for obj in self.selected_objects:
            # Apply rotation gradually
            obj.rotation_y += rotation_y
            
    def extrude_selected_faces(self, position, strength):
        """Extrude faces of selected objects"""
        if not self.selected_objects:
            return
            
        # Get hand height
        height = position.y
        
        for obj in self.selected_objects:
            if obj.model_name == 'cube':
                # Stretch cube in y direction based on hand height
                current_height = obj.scale.y
                target_height = max(0.1, height * strength * 2)
                
                # Smooth transition
                new_height = lerp(current_height, target_height, time.dt * 3)
                obj.scale = Vec3(obj.scale.x, new_height, obj.scale.z)
                
                # Move object to keep bottom face stationary
                height_diff = (new_height - current_height) / 2
                obj.y += height_diff
                
    def update_hover_highlight(self, all_objects):
        """Highlight object under cursor"""
        if not mouse.hovered_entity:
            if self.hover_object:
                # Remove highlight
                if self.hover_object not in self.selected_objects:
                    self.hover_object.color = self.hover_object.original_color
                self.hover_object = None
            return
            
        entity = mouse.hovered_entity
        
        # Only highlight our objects, not ground or UI elements
        if entity not in all_objects or entity in [e for e in self.grid_entities]:
            return
            
        # Store original color if not already highlighted
        if entity != self.hover_object:
            if self.hover_object and self.hover_object not in self.selected_objects:
                self.hover_object.color = self.hover_object.original_color
                
            if not hasattr(entity, 'original_color'):
                entity.original_color = entity.color
                
            if entity not in self.selected_objects:
                entity.color = color.light_gray
                
            self.hover_object = entity