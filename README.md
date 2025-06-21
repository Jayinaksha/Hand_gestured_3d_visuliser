# Hand_gestured_3d_visuliser
The repo is dedicated to making of an handgestured 3d cad designer and model simulator all by handgestures and a camera.

# Iron Man Hand Gesture 3D CAD System

A sophisticated hand gesture-controlled 3D creation system inspired by Tony Stark's holographic interface. Build, manipulate, and interact with 3D objects using just your hands and a webcam.

## Features

- **Gesture-Based Control**: No keyboard or mouse needed, control everything with hand gestures.
- **Dual-Mode System**: 
  - **Normal Mode**: Create drones, shoot, trigger explosions, and more.
  - **CAD Mode**: Precision tools for selecting, creating, moving, scaling, rotating, and extruding objects.
- **Real-Time Feedback**: Visual indicators show gesture recognition and tool selection.
- **Advanced Tracking**: Precision finger tracking with Kalman filtering for smooth interactions.
- **Modular Architecture**: Well-organized code structure makes it easy to extend and modify.

## Installation

### Prerequisites
- Python 3.8 or higher
- Webcam
- Sufficient lighting for hand tracking

### Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/jayinaksha/Hand_gestured_3d_visuliser.git
   cd HandGesture3DCreator
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install required packages:
   ```bash
   pip install ursina mediapipe opencv-python pygame numpy scipy filterpy
   ```

4. Run the application:
   ```bash
   python main.py
   ```

## Gesture Controls

### Mode Switching
- **All fingers extended**: Hold for 1 second to toggle between Normal and CAD modes.

### Normal Mode
- **Fist**: Spawn drone.
- **Peace Sign**: Shoot bullet.
- **Open Palm**: Camera control.
- **Pinch**: Spawn box.
- **Thumbs Up**: Rotate all objects.
- **Rock Sign**: Create explosion.

### CAD Mode Tool Selection
- **1 finger (index)**: SELECT tool.
- **2 fingers (peace)**: CREATE tool.
- **3 fingers**: MOVE tool.
- **4 fingers**: SCALE tool.
- **Rock sign (index + pinky)**: EXTRUDE tool.
- **Phone sign (thumb + index + pinky)**: ROTATE tool.

### CAD Tool Usage
- **SELECT**: Point at objects.
- **CREATE**: Point to place objects.
- **MOVE**: Pinch and move hand.
- **SCALE**: Spread/pinch fingers.
- **ROTATE**: Move hand left/right.
- **EXTRUDE**: Pinch and pull upward.

## Project Structure

- **main.py**: Entry point.
- **controller.py**: Main controller for managing gestures and actions.
- **precision_tracking.py**: Precision hand tracking module.
- **gesture_system.py**: Gesture recognition system.
- **cad_system.py**: CAD functionality (tools like select, create, move, etc.).
- **ui_manager.py**: UI handling for feedback and controls.

## Future Enhancements

- Add voice commands for tool selection and actions.
- Export CAD shapes to STL/OBJ files for 3D printing.
- AR/VR integration using phone or headset cameras.
- Upload custom 3D models for manipulation.

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

## Contributors

- **Jayinaksha Vyas** - Initial work
- Contributions are welcome! Open an issue or submit a pull request.