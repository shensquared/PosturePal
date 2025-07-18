#!/usr/bin/env python3
"""
Menu Bar Controller for PosturePal
Provides easy access to posture detection controls from the macOS menu bar
"""

import os
import sys
import subprocess
import json
import time
import re
from datetime import datetime, timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import rumps
except ImportError:
    print("rumps not found. Installing...")
    subprocess.run([sys.executable, "-m", "pip", "install", "rumps"])
    import rumps

CONFIG_FILE = "config.json"

def load_config():
    """Load configuration from file"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}
    else:
        return {}

def is_posture_detection_running():
    """Check if posture detection is running"""
    try:
        result = subprocess.run(['pgrep', '-f', 'pose_webcam.py'], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def get_sitting_time():
    """Get current sitting time from status file"""
    try:
        if not os.path.exists('posture_status.json'):
            return None, None, None
        
        with open('posture_status.json', 'r') as f:
            status = json.load(f)
        
        sitting_elapsed = status.get('sitting_elapsed', 0)
        is_sitting = status.get('is_sitting', False)
        window_visible = status.get('window_visible', False)
        
        if is_sitting and sitting_elapsed > 0:
            # Convert seconds to formatted time
            minutes = int(sitting_elapsed // 60)
            seconds = int(sitting_elapsed % 60)
            time_str = f"{minutes:02d}:{seconds:02d}"
            return sitting_elapsed, time_str, window_visible
        
        return None, None, window_visible
    except:
        return None, None, None

def toggle_camera_window():
    """Toggle camera window visibility"""
    try:
        # Send a signal to the posture detection process to toggle window
        # We'll use a simple file-based approach
        toggle_file = "toggle_window.txt"
        with open(toggle_file, 'w') as f:
            f.write(str(time.time()))
        
        # Give it a moment to process
        time.sleep(0.1)
        
        # Check if file was processed (deleted)
        if not os.path.exists(toggle_file):
            return True
        else:
            # Clean up if not processed
            try:
                os.remove(toggle_file)
            except:
                pass
            return False
    except:
        return False

def start_posture_detection():
    """Start posture detection"""
    try:
        result = subprocess.run(['python3', 'config_manager.py', '--start'], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Error starting posture detection: {e}")
        return False

def stop_posture_detection():
    """Stop posture detection"""
    try:
        result = subprocess.run(['python3', 'config_manager.py', '--stop'], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Error stopping posture detection: {e}")
        return False

class PosturePalMenuBar(rumps.App):
    def __init__(self):
        super().__init__("PosturePal", quit_button=None)
        self.config = load_config()
        self.setup_menu()
        self.sitting_time = None
        self.sitting_start_time = None
        
    def setup_menu(self):
        """Setup the menu bar items"""
        # Status indicator
        self.status_item = rumps.MenuItem("Status: Checking...")
        
        # Timer display
        self.timer_item = rumps.MenuItem("Timer: --:--")
        
        # Control buttons
        self.start_item = rumps.MenuItem("Start Posture Detection", callback=self.start_detection)
        self.stop_item = rumps.MenuItem("Stop Posture Detection", callback=self.stop_detection)
        
        # Camera window control
        self.camera_item = rumps.MenuItem("Show Camera Window", callback=self.toggle_camera)
        
        # Settings
        self.settings_item = rumps.MenuItem("Open Settings", callback=self.open_settings)
        
        # Calibration
        self.calibrate_item = rumps.MenuItem("Run Calibration", callback=self.run_calibration)
        
        # Quit
        self.quit_item = rumps.MenuItem("Quit PosturePal", callback=self.quit_app)
        
        # Add all items to the menu
        self.menu = [
            self.status_item,
            self.timer_item,
            None,  # Separator
            self.start_item,
            self.stop_item,
            self.camera_item,
            None,  # Separator
            self.settings_item,
            self.calibrate_item,
            None,  # Separator
            self.quit_item
        ]
        
        # Start status update timer
        self.timer = rumps.Timer(self.update_status, 2)  # Update every 2 seconds
        self.timer.start()
        
    def update_status(self, _):
        """Update the status indicator"""
        if is_posture_detection_running():
            self.status_item.title = "Status: 🟢 Running"
            self.start_item.set_callback(None)  # Disable start
            self.stop_item.set_callback(self.stop_detection)  # Enable stop
            
            # Update timer and camera window status
            sitting_elapsed, time_str, window_visible = get_sitting_time()
            if time_str:
                self.timer_item.title = f"Timer: {time_str}"
            else:
                self.timer_item.title = "Timer: --:--"
            
            # Update camera window button
            if window_visible:
                self.camera_item.title = "Hide Camera Window"
            else:
                self.camera_item.title = "Show Camera Window"
        else:
            self.status_item.title = "Status: 🔴 Stopped"
            self.start_item.set_callback(self.start_detection)  # Enable start
            self.stop_item.set_callback(None)  # Disable stop
            self.timer_item.title = "Timer: --:--"
            self.camera_item.title = "Show Camera Window"
    
    def start_detection(self, _):
        """Start posture detection"""
        if start_posture_detection():
            rumps.notification(
                title="PosturePal",
                subtitle="Posture Detection Started",
                message="Posture detection is now running in the background."
            )
        else:
            rumps.notification(
                title="PosturePal",
                subtitle="Error",
                message="Failed to start posture detection. Check the logs."
            )
    
    def stop_detection(self, _):
        """Stop posture detection"""
        if stop_posture_detection():
            rumps.notification(
                title="PosturePal",
                subtitle="Posture Detection Stopped",
                message="Posture detection has been stopped."
            )
        else:
            rumps.notification(
                title="PosturePal",
                subtitle="Error",
                message="Failed to stop posture detection."
            )
    
    def open_settings(self, _):
        """Open the settings GUI"""
        try:
            subprocess.Popen([sys.executable, 'run_gui.py'])
        except Exception as e:
            rumps.notification(
                title="PosturePal",
                subtitle="Error",
                message=f"Failed to open settings: {e}"
            )
    
    def toggle_camera(self, _):
        """Toggle camera window visibility"""
        if is_posture_detection_running():
            if toggle_camera_window():
                rumps.notification(
                    title="PosturePal",
                    subtitle="Camera Window",
                    message="Camera window visibility toggled."
                )
            else:
                rumps.notification(
                    title="PosturePal",
                    subtitle="Error",
                    message="Failed to toggle camera window."
                )
        else:
            rumps.notification(
                title="PosturePal",
                subtitle="Not Running",
                message="Posture detection must be running to toggle camera window."
            )
    
    def run_calibration(self, _):
        """Run calibration mode"""
        try:
            config = load_config()
            camera_index = config.get('camera_index', 0)
            subprocess.Popen([sys.executable, 'pose_webcam.py', '--calibrate', '--camera-index', str(camera_index)])
        except Exception as e:
            rumps.notification(
                title="PosturePal",
                subtitle="Error",
                message=f"Failed to start calibration: {e}"
            )
    
    def quit_app(self, _):
        """Quit the menu bar app and stop posture detection"""
        # Stop posture detection before quitting
        stop_posture_detection()
        rumps.quit_application()

def main():
    """Main function"""
    # Hide dock icon for menu bar app on macOS
    import os
    import sys
    
    # Set environment variable to hide dock icon
    os.environ['PYTHON_DISABLE_DOCK_ICON'] = '1'
    
    # Additional macOS-specific dock hiding
    if sys.platform == 'darwin':
        try:
            import AppKit
            # Hide dock icon
            AppKit.NSApplication.sharedApplication()
            AppKit.NSApp.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)
        except ImportError:
            # AppKit not available, use alternative method
            pass
    
    app = PosturePalMenuBar()
    app.run()

if __name__ == "__main__":
    main() 