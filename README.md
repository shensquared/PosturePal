# SitStraight - Posture Detection System

A smart posture detection system that helps you maintain good sitting posture and reminds you to take breaks.

## Features

- **Real-time posture detection** using MediaPipe
- **Personalized calibration** for your specific posture
- **Configurable alerts** with adjustable timing
- **Sitting timer** with visual progress bar
- **Auto-start on login** (optional)
- **Monitor detection** (optional - pauses when monitor is off)
- **Continuous voice alerts** until posture improves
- **Hidden dock icon** for clean desktop experience

## Quick Start

### 1. Install Dependencies
```bash
# Create and activate virtual environment
python3.10 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Calibrate Your Posture
```bash
python pose_webcam.py --calibrate
```
Follow the on-screen instructions to add good and bad posture examples.

### 3. Start Posture Detection
```bash
python pose_webcam.py
```

## Configuration Management

### GUI Configuration (Recommended)
For easy configuration through a graphical interface:

```bash
python config_gui.py
```

The GUI provides:
- ✅ **Real-time status** of all features
- 🎛️ **Easy toggles** for auto-start and monitor detection
- ⚙️ **Adjustable settings** with spinboxes and sliders
- 🎮 **One-click controls** to start/stop posture detection
- 📝 **Activity log** showing recent actions
- 🔧 **Calibration launcher** for posture training

### Command Line Configuration
For advanced users or scripting:

#### Show Current Configuration
```bash
python config_manager.py --show
```

#### Toggle Auto-Start on Login
```bash
python config_manager.py --toggle-auto-start
```

#### Toggle Monitor Detection
```bash
python config_manager.py --toggle-monitor
```

#### Start/Stop Posture Detection
```bash
python config_manager.py --start
python config_manager.py --stop
```

#### Adjust Alert Duration
```bash
python config_manager.py --alert-duration 3.0  # 3 seconds
```

#### Change Camera Index
```bash
python config_manager.py --camera 1  # Use camera index 1
```

## Configuration Options

| Setting | Default | Description |
|---------|---------|-------------|
| `auto_start_enabled` | `false` | Start automatically on login |
| `monitor_detection_enabled` | `false` | Pause when monitor is off |
| `alert_duration_seconds` | `5.0` | Time before first bad posture alert |
| `camera_index` | `0` | Camera device to use |
| `sitting_duration_threshold` | `1200` | Sitting time before break reminder (20 min) |
| `bad_posture_duration_threshold` | `60` | Bad posture time before "stand up" alert |
| `announcement_interval` | `5` | Seconds between continuous alerts |

## Manual Setup (Alternative)

If you prefer manual setup:

### Enable Auto-Start
```bash
./setup_autostart.sh
```

### Disable Auto-Start
```bash
launchctl unload ~/Library/LaunchAgents/com.sitstraight.posture.plist
rm ~/Library/LaunchAgents/com.sitstraight.posture.plist
```

## Troubleshooting

### Camera Issues
- Try different camera indices: `python pose_webcam.py --camera-index 1`
- Check camera permissions in System Settings

### Performance Issues
- Reduce frame rate by adjusting camera settings
- Close other applications using the camera

### Audio Issues
- Check system volume and audio output settings
- Ensure text-to-speech is enabled in macOS

## File Structure

```
sitstraight/
├── pose_webcam.py              # Main posture detection script
├── run_gui.py                  # GUI configuration interface
├── config_manager.py           # Command-line configuration tool
├── config.json                 # Configuration file
├── posture_calibration.json    # Personalized calibration data
├── simple_posture_launcher.sh  # Launcher script
├── setup_autostart.sh          # Auto-start setup script
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Requirements

- macOS 10.15 or later
- Python 3.10
- Webcam
- Microphone (for voice alerts)
 