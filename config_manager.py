#!/usr/bin/env python3
"""
Configuration manager for SitStraight posture detection system
"""

import json
import os
import subprocess
import sys
import argparse

CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "auto_start_enabled": False,
    "monitor_detection_enabled": False,
    "alert_duration_seconds": 5.0,
    "camera_index": 0,
    "sitting_duration_threshold": 1200,
    "bad_posture_duration_threshold": 60,
    "announcement_interval": 5
}

def load_config():
    """Load configuration from file"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # Merge with defaults to ensure all keys exist
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception as e:
            print(f"Error loading config: {e}")
            return DEFAULT_CONFIG.copy()
    else:
        return DEFAULT_CONFIG.copy()

def save_config(config):
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Configuration saved to {CONFIG_FILE}")
    except Exception as e:
        print(f"Error saving config: {e}")

def show_config(config):
    """Display current configuration"""
    print("\n=== SitStraight Configuration ===")
    print(f"Auto-start on login: {'✅ Enabled' if config['auto_start_enabled'] else '❌ Disabled'}")
    print(f"Monitor detection: {'✅ Enabled' if config['monitor_detection_enabled'] else '❌ Disabled'}")
    print(f"Alert duration: {config['alert_duration_seconds']} seconds")
    print(f"Camera index: {config['camera_index']}")
    print(f"Sitting threshold: {config['sitting_duration_threshold']} seconds ({config['sitting_duration_threshold']//60} minutes)")
    print(f"Bad posture threshold: {config['bad_posture_duration_threshold']} seconds")
    print(f"Announcement interval: {config['announcement_interval']} seconds")
    print()

def toggle_auto_start():
    """Toggle auto-start on login"""
    config = load_config()
    config['auto_start_enabled'] = not config['auto_start_enabled']
    
    if config['auto_start_enabled']:
        print("Enabling auto-start on login...")
        # Create and load LaunchAgent
        create_launch_agent()
        subprocess.run(['launchctl', 'load', os.path.expanduser('~/Library/LaunchAgents/com.sitstraight.posture.plist')])
        print("✅ Auto-start enabled")
    else:
        print("Disabling auto-start on login...")
        # Unload and remove LaunchAgent
        subprocess.run(['launchctl', 'unload', os.path.expanduser('~/Library/LaunchAgents/com.sitstraight.posture.plist')], 
                      capture_output=True)
        try:
            os.remove(os.path.expanduser('~/Library/LaunchAgents/com.sitstraight.posture.plist'))
        except FileNotFoundError:
            pass
        print("✅ Auto-start disabled")
    
    save_config(config)

def toggle_monitor_detection():
    """Toggle monitor detection feature"""
    config = load_config()
    config['monitor_detection_enabled'] = not config['monitor_detection_enabled']
    
    if config['monitor_detection_enabled']:
        print("✅ Monitor detection enabled")
        print("Note: This will pause posture detection when monitor is off")
    else:
        print("✅ Monitor detection disabled")
        print("Note: Posture detection will run continuously")
    
    save_config(config)

def create_launch_agent():
    """Create LaunchAgent plist file"""
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.sitstraight.posture</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>{os.path.abspath('simple_posture_launcher.sh')}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{os.path.expanduser('~/Library/Logs/sitstraight.log')}</string>
    <key>StandardErrorPath</key>
    <string>{os.path.expanduser('~/Library/Logs/sitstraight.log')}</string>
    <key>LSUIElement</key>
    <true/>
    <key>HideDockIcon</key>
    <true/>
</dict>
</plist>"""
    
    # Ensure LaunchAgents directory exists
    launch_agents_dir = os.path.expanduser('~/Library/LaunchAgents')
    os.makedirs(launch_agents_dir, exist_ok=True)
    
    # Write plist file
    plist_path = os.path.join(launch_agents_dir, 'com.sitstraight.posture.plist')
    with open(plist_path, 'w') as f:
        f.write(plist_content)
    
    print(f"LaunchAgent created at {plist_path}")

def start_posture_detection():
    """Start posture detection manually"""
    print("Starting posture detection...")
    config = load_config()
    
    # Kill any existing processes
    subprocess.run(['pkill', '-f', 'pose_webcam.py'], capture_output=True)
    subprocess.run(['pkill', '-f', 'simple_posture_launcher.sh'], capture_output=True)
    
    # Start the launcher
    subprocess.Popen(['/bin/bash', 'simple_posture_launcher.sh'])
    print("✅ Posture detection started")

def stop_posture_detection():
    """Stop posture detection"""
    print("Stopping posture detection...")
    subprocess.run(['pkill', '-f', 'pose_webcam.py'], capture_output=True)
    subprocess.run(['pkill', '-f', 'simple_posture_launcher.sh'], capture_output=True)
    print("✅ Posture detection stopped")

def main():
    parser = argparse.ArgumentParser(description='SitStraight Configuration Manager')
    parser.add_argument('--show', action='store_true', help='Show current configuration')
    parser.add_argument('--toggle-auto-start', action='store_true', help='Toggle auto-start on login')
    parser.add_argument('--toggle-monitor', action='store_true', help='Toggle monitor detection')
    parser.add_argument('--start', action='store_true', help='Start posture detection manually')
    parser.add_argument('--stop', action='store_true', help='Stop posture detection')
    parser.add_argument('--alert-duration', type=float, help='Set alert duration in seconds')
    parser.add_argument('--camera', type=int, help='Set camera index')
    
    args = parser.parse_args()
    
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    config = load_config()
    
    if args.show:
        show_config(config)
    
    if args.toggle_auto_start:
        toggle_auto_start()
    
    if args.toggle_monitor:
        toggle_monitor_detection()
    
    if args.start:
        start_posture_detection()
    
    if args.stop:
        stop_posture_detection()
    
    if args.alert_duration is not None:
        config['alert_duration_seconds'] = args.alert_duration
        save_config(config)
        print(f"Alert duration set to {args.alert_duration} seconds")
    
    if args.camera is not None:
        config['camera_index'] = args.camera
        save_config(config)
        print(f"Camera index set to {args.camera}")

if __name__ == "__main__":
    main() 