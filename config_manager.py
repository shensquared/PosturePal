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
    print("\n=== PosturePal Configuration ===")
    print(f"Auto-start on login: {'✅ Enabled' if config['auto_start_enabled'] else '❌ Disabled'}")
    print(f"Monitor detection: {'✅ Enabled' if config['monitor_detection_enabled'] else '❌ Disabled'}")
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
        subprocess.run(['launchctl', 'load', os.path.expanduser('~/Library/LaunchAgents/com.posturepal.posture.plist')])
        print("✅ Auto-start enabled")
    else:
        print("Disabling auto-start on login...")
        # Unload and remove LaunchAgent
        subprocess.run(['launchctl', 'unload', os.path.expanduser('~/Library/LaunchAgents/com.posturepal.posture.plist')], 
                      capture_output=True)
        try:
            os.remove(os.path.expanduser('~/Library/LaunchAgents/com.posturepal.posture.plist'))
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
    <string>com.posturepal.posture</string>
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
    <string>{os.path.expanduser('~/Library/Logs/posturepal.log')}</string>
    <key>StandardErrorPath</key>
    <string>{os.path.expanduser('~/Library/Logs/posturepal.log')}</string>
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
    plist_path = os.path.join(launch_agents_dir, 'com.posturepal.posture.plist')
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
    subprocess.run(['pkill', '-f', 'launch_posture_detection.sh'], capture_output=True)
    
    # Use the new launcher script with better dock icon hiding
    launcher_path = os.path.abspath('launch_posture_detection.sh')
    log_file = os.path.abspath('simple_posture.log')
    
    # Use nohup to ensure the process continues even if parent exits
    # The launcher script already sets the environment variables for dock hiding
    cmd = f"nohup /bin/bash {launcher_path} > {log_file} 2>&1 &"
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Give it a moment to start
    import time
    time.sleep(2)
    
    # Check if it's running
    if is_posture_detection_running():
        print("✅ Posture detection started (dock icon hidden)")
    else:
        print("❌ Failed to start posture detection")
        return False
    
    return True

def is_posture_detection_running():
    """Check if posture detection is running"""
    try:
        result = subprocess.run(['pgrep', '-f', 'pose_webcam.py'], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def stop_posture_detection():
    """Stop posture detection"""
    print("Stopping posture detection...")
    subprocess.run(['pkill', '-f', 'pose_webcam.py'], capture_output=True)
    subprocess.run(['pkill', '-f', 'simple_posture_launcher.sh'], capture_output=True)
    subprocess.run(['pkill', '-f', 'launch_posture_detection.sh'], capture_output=True)
    print("✅ Posture detection stopped")

def main():
    parser = argparse.ArgumentParser(description='PosturePal Configuration Manager')
    parser.add_argument('--show', action='store_true', help='Show current configuration')
    parser.add_argument('--toggle-auto-start', action='store_true', help='Toggle auto-start on login')
    parser.add_argument('--toggle-monitor', action='store_true', help='Toggle monitor detection')
    parser.add_argument('--start', action='store_true', help='Start posture detection manually')
    parser.add_argument('--stop', action='store_true', help='Stop posture detection')
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
    
    if args.camera is not None:
        config['camera_index'] = args.camera
        save_config(config)
        print(f"Camera index set to {args.camera}")

if __name__ == "__main__":
    main() 