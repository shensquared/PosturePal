#!/usr/bin/env python3
"""
Wrapper script to run the GUI using system Python (which has tkinter)
but delegate posture detection to the virtual environment Python
"""

import os
import sys
import subprocess
import json

# Configuration file path
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

def save_config(config):
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def run_venv_command(cmd):
    """Run a command in the virtual environment"""
    venv_python = os.path.join(os.getcwd(), '.venv', 'bin', 'python')
    full_cmd = [venv_python] + cmd
    return subprocess.run(full_cmd, capture_output=True, text=True)

def main():
    # Import tkinter (available in system Python)
    import tkinter as tk
    from tkinter import ttk, messagebox
    
    class SitStraightConfigGUI:
        def __init__(self, root):
            self.root = root
            self.root.title("SitStraight Configuration")
            self.root.minsize(600, 850)  # Slightly taller minimum
            self.root.geometry("600x850")  # Slightly taller window
            self.root.resizable(False, False)
            
            # Load configuration
            self.config = load_config()
            
            # Create GUI elements
            self.create_widgets()
            
            # Set up periodic status updates
            self.update_button_states()
            self.root.after(5000, self.periodic_status_check)  # Check every 5 seconds
        
        def create_widgets(self):
            """Create all GUI widgets"""
            # Main frame
            main_frame = ttk.Frame(self.root, padding="20 20 20 120")
            main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            # Configure grid weights for expansion
            self.root.grid_rowconfigure(0, weight=1)
            self.root.grid_columnconfigure(0, weight=1)
            for i in range(4):  # Reduced from 5 to 4 since we removed status section
                main_frame.grid_rowconfigure(i, weight=0)
            main_frame.grid_rowconfigure(4, weight=1, minsize=180)  # Log section is now row 4
            main_frame.grid_columnconfigure(0, weight=1)
            main_frame.grid_columnconfigure(1, weight=1)
            
            # Title
            title_label = ttk.Label(main_frame, text="SitStraight Configuration", 
                                   font=("Arial", 16, "bold"))
            title_label.grid(row=0, column=0, columnspan=2, pady=(0, 30))
            
            # Toggle buttons section (now row 1)
            self.create_toggle_section(main_frame, 1)
            
            # Settings section (now row 2)
            self.create_settings_section(main_frame, 2)
            
            # Control buttons section (now row 3)
            self.create_control_section(main_frame, 3)
            
            # Log section (now row 4)
            self.create_log_section(main_frame, 4)
        
        def create_toggle_section(self, parent, row):
            """Create toggle buttons section"""
            toggle_frame = ttk.LabelFrame(parent, text="Features", padding="10")
            toggle_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))  # More space below
            
            self.auto_start_var = tk.BooleanVar(value=self.config.get('auto_start_enabled', False))
            auto_start_check = ttk.Checkbutton(toggle_frame, text="Start automatically on login", 
                                              variable=self.auto_start_var, 
                                              command=self.toggle_auto_start)
            auto_start_check.grid(row=0, column=0, sticky=tk.W, pady=2)
            
            self.monitor_var = tk.BooleanVar(value=self.config.get('monitor_detection_enabled', False))
            monitor_check = ttk.Checkbutton(toggle_frame, text="Pause app when user is idle (2+ min)", 
                                           variable=self.monitor_var, 
                                           command=self.toggle_monitor_detection)
            monitor_check.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        def create_settings_section(self, parent, row):
            """Create settings section"""
            settings_frame = ttk.LabelFrame(parent, text="Settings", padding="10")
            settings_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))  # More space below
            
            # Alert duration
            ttk.Label(settings_frame, text="Alert duration (seconds):").grid(row=0, column=0, sticky=tk.W, pady=2)
            self.alert_duration_var = tk.DoubleVar(value=self.config.get('alert_duration_seconds', 5.0))
            alert_duration_spin = ttk.Spinbox(settings_frame, from_=1.0, to=30.0, increment=0.5, 
                                             textvariable=self.alert_duration_var, width=10)
            alert_duration_spin.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
            
            # Camera index
            ttk.Label(settings_frame, text="Camera index:").grid(row=1, column=0, sticky=tk.W, pady=2)
            self.camera_var = tk.IntVar(value=self.config.get('camera_index', 0))
            camera_spin = ttk.Spinbox(settings_frame, from_=0, to=10, increment=1, 
                                     textvariable=self.camera_var, width=10)
            camera_spin.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
            
            # Sitting duration
            ttk.Label(settings_frame, text="Sitting duration (minutes):").grid(row=2, column=0, sticky=tk.W, pady=2)
            sitting_seconds = self.config.get('sitting_duration_threshold', 1200)
            self.sitting_duration_var = tk.IntVar(value=sitting_seconds // 60)
            sitting_duration_spin = ttk.Spinbox(settings_frame, from_=5, to=60, increment=5, 
                                               textvariable=self.sitting_duration_var, width=10)
            sitting_duration_spin.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=2)
            
            # Bad posture duration
            ttk.Label(settings_frame, text="Bad posture duration (seconds):").grid(row=3, column=0, sticky=tk.W, pady=2)
            self.bad_posture_duration_var = tk.IntVar(value=self.config.get('bad_posture_duration_threshold', 60))
            bad_posture_duration_spin = ttk.Spinbox(settings_frame, from_=30, to=300, increment=10, 
                                                   textvariable=self.bad_posture_duration_var, width=10)
            bad_posture_duration_spin.grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=2)
            
            # Announcement interval
            ttk.Label(settings_frame, text="Announcement interval (seconds):").grid(row=4, column=0, sticky=tk.W, pady=2)
            self.announcement_interval_var = tk.IntVar(value=self.config.get('announcement_interval', 5))
            announcement_interval_spin = ttk.Spinbox(settings_frame, from_=1, to=30, increment=1, 
                                                    textvariable=self.announcement_interval_var, width=10)
            announcement_interval_spin.grid(row=4, column=1, sticky=tk.W, padx=(10, 0), pady=2)
            
            # Save settings button
            save_btn = ttk.Button(settings_frame, text="Save Settings", command=self.save_settings)
            save_btn.grid(row=5, column=0, columnspan=2, pady=(10, 0))
        
        def create_control_section(self, parent, row):
            """Create control buttons section"""
            # Control frame
            control_frame = ttk.LabelFrame(parent, text="Controls", padding="10")
            control_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 30))  # More space below controls
            control_frame.grid_rowconfigure(0, minsize=80)  # Minimum height for controls
            
            # Configure columns for equal spacing
            control_frame.grid_columnconfigure(0, weight=1)
            control_frame.grid_columnconfigure(1, weight=1)
            control_frame.grid_columnconfigure(2, weight=1)
            
            self.start_btn = ttk.Button(control_frame, text="Start Posture Detection", 
                                       command=self.start_posture_detection)
            self.start_btn.grid(row=0, column=0, padx=(0, 5), pady=5, sticky=(tk.W, tk.E))
            
            self.stop_btn = ttk.Button(control_frame, text="Stop Posture Detection", 
                                      command=self.stop_posture_detection)
            self.stop_btn.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
            
            calibrate_btn = ttk.Button(control_frame, text="Run Calibration", 
                                      command=self.run_calibration)
            calibrate_btn.grid(row=0, column=2, padx=(5, 0), pady=5, sticky=(tk.W, tk.E))
        
        def create_log_section(self, parent, row):
            """Create log display section"""
            # Log frame
            log_frame = ttk.LabelFrame(parent, text="Recent Activity", padding="10")
            log_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
            
            # Configure grid weights for expansion
            log_frame.grid_rowconfigure(0, weight=1, minsize=80)  # Minimum height for log
            log_frame.grid_columnconfigure(0, weight=1)
            
            # Log text area
            self.log_text = tk.Text(log_frame, height=5, width=70, wrap=tk.WORD)  # Taller text area
            self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
            scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
            self.log_text.configure(yscrollcommand=scrollbar.set)
            
            clear_log_btn = ttk.Button(log_frame, text="Clear Log", command=self.clear_log)
            clear_log_btn.grid(row=1, column=0, pady=(5, 0))
        
        def log_message(self, message):
            """Add message to log"""
            self.log_text.insert(tk.END, f"{message}\n")
            self.log_text.see(tk.END)
        
        def clear_log(self):
            """Clear log messages"""
            self.log_text.delete(1.0, tk.END)
        
        def is_process_running(self):
            """Check if posture detection is running"""
            try:
                result = subprocess.run(['pgrep', '-f', 'pose_webcam.py'], 
                                      capture_output=True, text=True)
                return result.returncode == 0
            except:
                return False
        
        def update_button_states(self):
            """Update button states based on process status"""
            if self.is_process_running():
                self.start_btn.config(state="disabled")
                self.stop_btn.config(state="normal")
            else:
                self.start_btn.config(state="normal")
                self.stop_btn.config(state="disabled")
        
        def periodic_status_check(self):
            """Periodically check and update status"""
            self.update_button_states()
            # Schedule next check
            self.root.after(5000, self.periodic_status_check)
        
        def toggle_auto_start(self):
            """Toggle auto-start on login"""
            self.config['auto_start_enabled'] = self.auto_start_var.get()
            
            if self.config['auto_start_enabled']:
                self.log_message("Enabling auto-start on login...")
                # Use venv Python to create launch agent
                result = run_venv_command(['config_manager.py', '--toggle-auto-start'])
                if result.returncode == 0:
                    self.log_message("✅ Auto-start enabled")
                else:
                    self.log_message(f"❌ Error: {result.stderr}")
                    self.auto_start_var.set(False)
                    self.config['auto_start_enabled'] = False
            else:
                self.log_message("Disabling auto-start on login...")
                result = run_venv_command(['config_manager.py', '--toggle-auto-start'])
                if result.returncode == 0:
                    self.log_message("✅ Auto-start disabled")
                else:
                    self.log_message(f"❌ Error: {result.stderr}")
            
            save_config(self.config)
        
        def toggle_monitor_detection(self):
            """Toggle user idle detection feature"""
            self.config['monitor_detection_enabled'] = self.monitor_var.get()
            
            if self.config['monitor_detection_enabled']:
                self.log_message("✅ User idle detection enabled (pauses after 2+ min inactive)")
            else:
                self.log_message("✅ User idle detection disabled")
            
            save_config(self.config)
        
        def save_settings(self):
            """Save all settings"""
            self.config['alert_duration_seconds'] = self.alert_duration_var.get()
            self.config['camera_index'] = self.camera_var.get()
            self.config['sitting_duration_threshold'] = self.sitting_duration_var.get() * 60
            self.config['bad_posture_duration_threshold'] = self.bad_posture_duration_var.get()
            self.config['announcement_interval'] = self.announcement_interval_var.get()
            
            if save_config(self.config):
                self.log_message("✅ Settings saved successfully")
            else:
                self.log_message("❌ Error saving settings")
        
        def start_posture_detection(self):
            """Start posture detection"""
            self.log_message("Starting posture detection...")
            result = run_venv_command(['config_manager.py', '--start'])
            if result.returncode == 0:
                self.log_message("✅ Posture detection started")
                # Update button states after a short delay to allow process to start
                self.root.after(2000, self.update_button_states)
            else:
                self.log_message(f"❌ Error: {result.stderr}")
                self.log_message("Try running calibration first to ensure camera works")
            self.update_button_states()
        
        def stop_posture_detection(self):
            """Stop posture detection"""
            self.log_message("Stopping posture detection...")
            result = run_venv_command(['config_manager.py', '--stop'])
            if result.returncode == 0:
                self.log_message("✅ Posture detection stopped")
            else:
                self.log_message(f"❌ Error: {result.stderr}")
            self.update_button_states()
        
        def run_calibration(self):
            """Run calibration mode"""
            self.log_message("Starting calibration mode...")
            # Get the current camera index from config
            camera_index = self.config.get('camera_index', 0)
            self.log_message(f"Using camera index {camera_index} from configuration")
            result = run_venv_command(['pose_webcam.py', '--calibrate', '--camera-index', str(camera_index)])
            if result.returncode == 0:
                self.log_message("✅ Calibration mode started")
            else:
                self.log_message(f"❌ Error: {result.stderr}")
    
    # Create and run the GUI
    root = tk.Tk()
    app = SitStraightConfigGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 