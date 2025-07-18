# PosturePal - Posture Detection for macOS

A smart posture detection system that uses your webcam to monitor your sitting posture and provides voice alerts to help you maintain good posture and take regular breaks.

## ✨ Features

- **Real-time Posture Detection**: Uses MediaPipe to detect your sitting posture through your webcam
- **Voice Alerts**: Speaks "sit straight" when you slouch and "please stand up" after 20 minutes of sitting
- **Menu Bar Interface**: Clean macOS menu bar app for easy control
- **Mirrored Camera View**: See yourself like a mirror during calibration
- **Smart Voice Queue**: Prevents overlapping voice announcements
- **Configurable Settings**: Adjust camera, timing, and alert preferences
- **Auto-start Option**: Can start automatically when you log in
- **User Idle Detection**: Automatically pauses when user is inactive for 2+ minutes, resumes when active

## 🚀 Quick Start

### 1. Install Python 3.10 (Required)
PosturePal requires Python 3.8-3.11 for MediaPipe compatibility. We recommend Python 3.10:

```bash
# Install Python 3.10 using Homebrew
brew install python@3.10

# Install tkinter for Python 3.10 (required for GUI)
brew install python-tk@3.10
```

### 2. Install Dependencies
```bash
# Create and activate virtual environment with Python 3.10
python3.10 -m venv .venv
source .venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

**Quick Reference:**
```bash
# If you need to reinstall dependencies
pip install --upgrade -r requirements.txt

# If you need to check installed packages
pip list | grep -E "(opencv|mediapipe|numpy|pyttsx3|rumps)"
```

### 3. Start the Menu Bar App
```bash
./start.sh
```

That's it! The PosturePal menu bar icon will appear in your macOS menu bar.

## 🎯 How to Use

### Menu Bar Controls
- **Status Indicator**: Shows if posture detection is running (🟢 Running / 🔴 Stopped)
- **Start Posture Detection**: Begin monitoring your posture
- **Stop Posture Detection**: Stop monitoring
- **Open Settings**: Configure camera, timing, and other preferences
- **Run Calibration**: Set up your good posture position
- **Quit PosturePal**: Stop everything and quit the menu bar app

### First Time Setup
1. Run `./start.sh` to launch the menu bar
2. Click **"Run Calibration"** to set up your good posture position
3. Click **"Start Posture Detection"** to begin monitoring
4. Use **"Open Settings"** to adjust camera index if needed

## ⚙️ Configuration

### Settings (via Menu Bar → Open Settings)
- **Camera Index**: Which camera to use (default: 2)
- **Sitting Duration**: Minutes before "stand up" alert (default: 20 minutes)
- **Bad Posture Duration**: Seconds of slouching before "sit straight" alert (default: 60 seconds)
- **Alert Duration**: How long voice alerts play (default: 5 seconds)
- **Announcement Interval**: Time between repeated alerts (default: 5 seconds)
- **Start automatically on login**: Start posture detection when you log into your Mac
- **Pause when user is idle**: Automatically pause when user is inactive for 2+ minutes

### Camera Setup
If the default camera (index 2) doesn't work:
1. Open Settings from the menu bar
2. Try different camera indices (0, 1, 2, etc.)
3. Click "Save Settings"
4. Restart posture detection

## 🔧 Troubleshooting

### Python Version Issues
- **Error: "No module named '_tkinter'"**: Install tkinter for Python 3.10: `brew install python-tk@3.10`
- **Error: "No matching distribution found for mediapipe"**: Ensure you're using Python 3.8-3.11 (recommend 3.10)
- **Wrong Python version**: Use `python3.10 -m venv .venv` to create virtual environment with correct Python version

### Voice Alerts Not Playing
- Check your system volume
- Ensure microphone permissions are granted
- Try restarting posture detection from the menu bar

### Camera Not Working
- Try different camera indices in Settings
- Check camera permissions in System Preferences
- Ensure no other app is using the camera

### Menu Bar Not Appearing
- Check if the script has execute permissions: `chmod +x start.sh`
- Look for error messages in `menu_bar.log`
- Try running manually: `python3 menu_bar_controller.py`
- Ensure you're using Python 3.10 in your virtual environment

### Posture Detection Issues
- Run calibration again to reset your good posture position
- Check `simple_posture.log` for error messages
- Ensure good lighting for camera detection

## 📁 File Structure

```
posturepal/
├── start.sh                    # Launch the menu bar app
├── pose_webcam.py             # Core posture detection engine
├── menu_bar_controller.py     # Menu bar interface
├── config_manager.py          # Configuration management
├── run_gui.py                 # Settings GUI
├── simple_posture_launcher.sh # Posture detection launcher
├── config.json                # Configuration file
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🎮 Voice Commands

The system provides two types of voice alerts:

1. **"Sit straight"** - Triggered when you slouch for 60 seconds
2. **"Please stand up"** - Triggered after sitting for 20 minutes

Voice alerts are queued to prevent overlapping announcements and ensure clear audio playback.

## 🔄 Auto-start & User Idle Detection

### Auto-start on Login
To enable auto-start on login:
1. Open Settings from the menu bar
2. Check "Start automatically on login"
3. The system will create a macOS LaunchAgent

To disable auto-start:
1. Open Settings from the menu bar
2. Uncheck "Start automatically on login"

### User Idle Detection
To pause detection when you're away from your computer:
1. Open Settings from the menu bar
2. Check "Pause when user is idle (2+ min)"
3. Detection will automatically pause when you're inactive for 2+ minutes and resume when you return

Both features work together - you can have auto-start enabled and idle detection enabled for optimal behavior.

## 📝 Logs

- `menu_bar.log` - Menu bar app activity
- `simple_posture.log` - Posture detection activity
- `~/Library/Logs/posturepal.log` - Auto-start logs (if enabled)

## 🛠️ Development

### Running Components Separately
```bash
# Run posture detection directly
python3 pose_webcam.py

# Run menu bar only
python3 menu_bar_controller.py

# Run settings GUI only
python3 run_gui.py

# Manage configuration
python3 config_manager.py --show
```

### Virtual Environment
The system uses a virtual environment (`.venv/`) to manage dependencies. Always activate it before running:
```bash
source .venv/bin/activate
```

**Note**: Make sure your virtual environment is created with Python 3.10:
```bash
python3.10 -m venv .venv
```

### Dependency Management
- **Automatic Installation**: All Python dependencies are installed via `pip install -r requirements.txt`
- **Version Pinning**: Dependencies use minimum version requirements for compatibility
- **System Dependencies**: Some dependencies (like tkinter) require system-level installation via Homebrew
- **MediaPipe Compatibility**: MediaPipe has strict Python version requirements (3.8-3.11)

### Common Dependency Issues
- **MediaPipe Installation Fails**: Ensure Python version is 3.8-3.11
- **Tkinter Missing**: Install via `brew install python-tk@3.10`
- **Permission Issues**: Ensure you have write access to the project directory
- **Conflicting Packages**: Use virtual environment to avoid conflicts with system Python

## 📋 Requirements

### System Requirements
- macOS 10.14 or later
- Python 3.8-3.11 (Python 3.10 recommended for best compatibility)
- Homebrew (for installing Python 3.10 and tkinter)
- Webcam
- Microphone (for voice alerts)

### Python Dependencies
The following packages are automatically installed via `requirements.txt`:

**Core Dependencies:**
- `opencv-python>=4.8.0` - Computer vision and webcam access
- `mediapipe>=0.10.0` - Pose detection and body tracking
- `numpy>=1.24.0` - Numerical computing
- `pyttsx3>=2.90` - Text-to-speech for voice alerts

**macOS Integration:**
- `rumps>=0.4.0` - macOS menu bar integration
- `pyobjc-framework-Cocoa>=9.0` - macOS native framework access

**Additional Dependencies (auto-installed):**
- `tkinter` - GUI framework (installed via Homebrew)
- Various MediaPipe dependencies (JAX, matplotlib, etc.)
- PyObjC frameworks for macOS integration

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📄 License

This project is open source and available under the MIT License.
 