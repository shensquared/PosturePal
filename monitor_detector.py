#!/usr/bin/env python3
"""
Monitor State Detector for macOS
Detects when monitor is turned on/off and manages posture detection accordingly
"""

import subprocess
import time
import signal
import sys
import os
import json
from datetime import datetime

class MonitorDetector:
    def __init__(self, log_file="monitor_detection.log"):
        self.log_file = log_file
        self.running = True
        self.monitor_on = True
        self.posture_process = None
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def log_message(self, message):
        """Log a message with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"{timestamp} - {message}"
        print(log_entry)
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry + '\n')
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.log_message(f"Received signal {signum}, shutting down...")
        self.running = False
        if self.posture_process:
            self.stop_posture_detection()
        sys.exit(0)
    
    def is_monitor_on(self):
        """Check if monitor is currently on"""
        try:
            # Method 1: Check display brightness
            result = subprocess.run(['brightnessctl', 'get'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                brightness = int(result.stdout.strip())
                return brightness > 0
            
            # Method 2: Check if displays are active
            result = subprocess.run(['system_profiler', 'SPDisplaysDataType'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                # Look for active displays
                if 'Resolution:' in result.stdout:
                    return True
            
            # Method 3: Check if any display is connected
            result = subprocess.run(['ioreg', '-l'], 
                                  capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                # Look for display-related entries
                if 'IODisplayConnect' in result.stdout:
                    return True
            
            # Default to assuming monitor is on if we can't determine
            return True
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, ValueError):
            # If any method fails, assume monitor is on
            return True
    
    def start_posture_detection(self):
        """Start the posture detection script"""
        if self.posture_process and self.posture_process.poll() is None:
            self.log_message("Posture detection already running")
            return
        
        try:
            self.log_message("Starting posture detection...")
            
            # Change to the script directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            os.chdir(script_dir)
            
            # Start the posture detection script
            self.posture_process = subprocess.Popen([
                'bash', '-c', 
                'source .venv/bin/activate && python pose_webcam.py --camera-index 0'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.log_message(f"Posture detection started with PID: {self.posture_process.pid}")
            
        except Exception as e:
            self.log_message(f"Error starting posture detection: {e}")
    
    def stop_posture_detection(self):
        """Stop the posture detection script"""
        if self.posture_process and self.posture_process.poll() is None:
            self.log_message("Stopping posture detection...")
            try:
                self.posture_process.terminate()
                # Wait for graceful shutdown
                self.posture_process.wait(timeout=5)
                self.log_message("Posture detection stopped gracefully")
            except subprocess.TimeoutExpired:
                self.log_message("Force killing posture detection...")
                self.posture_process.kill()
                self.posture_process.wait()
            except Exception as e:
                self.log_message(f"Error stopping posture detection: {e}")
    
    def run(self):
        """Main monitoring loop"""
        self.log_message("Monitor detector started")
        
        # Initial monitor state check
        self.monitor_on = self.is_monitor_on()
        self.log_message(f"Initial monitor state: {'ON' if self.monitor_on else 'OFF'}")
        
        if self.monitor_on:
            self.start_posture_detection()
        
        # Main monitoring loop
        while self.running:
            try:
                # Check monitor state every 2 seconds
                current_monitor_state = self.is_monitor_on()
                
                # State change detected
                if current_monitor_state != self.monitor_on:
                    if current_monitor_state:
                        # Monitor turned ON
                        self.log_message("Monitor turned ON - starting posture detection")
                        self.monitor_on = True
                        self.start_posture_detection()
                    else:
                        # Monitor turned OFF
                        self.log_message("Monitor turned OFF - stopping posture detection")
                        self.monitor_on = False
                        self.stop_posture_detection()
                
                # Check if posture detection process is still running
                if self.posture_process and self.posture_process.poll() is not None:
                    if self.monitor_on:
                        self.log_message("Posture detection crashed, restarting...")
                        self.start_posture_detection()
                    else:
                        self.log_message("Posture detection stopped while monitor is off")
                        self.posture_process = None
                
                time.sleep(2)
                
            except KeyboardInterrupt:
                self.log_message("Keyboard interrupt received")
                break
            except Exception as e:
                self.log_message(f"Error in monitoring loop: {e}")
                time.sleep(5)
        
        # Cleanup
        self.log_message("Monitor detector shutting down...")
        if self.posture_process:
            self.stop_posture_detection()

if __name__ == "__main__":
    detector = MonitorDetector()
    detector.run() 