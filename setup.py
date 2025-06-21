#!/usr/bin/env python3
"""
Setup script for Iron Man CAD System
"""

import os
import sys
import subprocess
import platform

def print_colored(text, color='green'):
    colors = {
        'green': '\033[92m',
        'yellow': '\033[93m',
        'red': '\033[91m',
        'blue': '\033[94m',
        'end': '\033[0m'
    }
    print(f"{colors.get(color, '')}{text}{colors['end']}")

def create_venv():
    print_colored("Creating virtual environment...", "blue")
    if not os.path.exists('venv'):
        subprocess.run([sys.executable, "-m", "venv", "venv"])
    else:
        print_colored("Virtual environment already exists.", "yellow")

def install_packages():
    print_colored("Installing required packages...", "blue")
    
    # Get the correct pip path
    if platform.system() == "Windows":
        pip_path = os.path.join("venv", "Scripts", "pip")
    else:
        pip_path = os.path.join("venv", "bin", "pip")
    
    # Install packages
    packages = ["ursina", "mediapipe", "opencv-python", "pygame", "numpy", "scipy", "filterpy"]
    for package in packages:
        print_colored(f"Installing {package}...", "yellow")
        subprocess.run([pip_path, "install", package])

def create_files():
    print_colored("Creating project files...", "blue")
    
    # Create the files
    for filename, content in FILES.items():
        with open(filename, "w") as f:
            f.write(content)
        print_colored(f"Created {filename}", "green")
    
    # Make main.py executable on Unix systems
    if platform.system() != "Windows":
        os.chmod("main.py", 0o755)

def run_application():
    print_colored("\nSetup complete!", "green")
    print_colored("To run the application:", "yellow")
    
    if platform.system() == "Windows":
        print_colored("1. Activate the virtual environment: venv\\Scripts\\activate", "blue")
        print_colored("2. Run the application: python main.py", "blue")
    else:
        print_colored("1. Activate the virtual environment: source venv/bin/activate", "blue")
        print_colored("2. Run the application: python main.py", "blue")

if __name__ == "__main__":
    print_colored("===== Setting up Iron Man CAD System =====", "blue")
    
    try:
        create_venv()
        install_packages()
        create_files()
        run_application()
    except Exception as e:
        print_colored(f"Error during setup: {e}", "red")
        sys.exit(1)

# Define all files here
FILES = {
    "main.py": """#!/usr/bin/env python3
\"\"\"
Iron Man Hand Gesture 3D Controller - Main Entry Point
\"\"\"

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
""",
    # Add the rest of the files here as needed
}