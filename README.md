# SitStraight - Posture Detection System

A smart posture detection system that helps you maintain good sitting posture and reminds you to take breaks.

## Features

- **Real-time posture detection** using MediaPipe
- **Personalized calibration** for your specific posture
- **Configurable alerts** with adjustable timing
- **Sitting timer** with visual progress bar (20-minute default)
- **Voice conflict resolution** - prevents overlapping alerts
- **Mirrored camera view** for natural interaction
- **Auto-start on login** (optional)
- **Monitor detection** (optional - pauses when monitor is off)
- **Continuous voice alerts** until posture improves
- **Hidden dock icons** for clean desktop experience (menu bar and posture detection)
- **Enhanced window controls** with always-on-top
- **Menu bar integration** for easy access to controls
- **Multiple ways to quit** (keyboard, window close, menu bar)

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
python pose_webcam.py --camera-index 2
```

## Configuration Management

### GUI Configuration (Recommended)
For easy configuration through a graphical interface:

```bash
python run_gui.py
```

The GUI provides:
- ✅ **Real-time status** of all features
- 🎛️ **Easy toggles** for auto-start and monitor detection
- ⚙️ **Adjustable settings** with spinboxes and sliders
- 🎮 **One-click controls** to start/stop posture detection
- 📝 **Activity log** showing recent actions
- 🔧 **Calibration launcher** for posture training

### Menu Bar Integration
For quick access to controls from the macOS menu bar:

```bash
./start_menu_bar.sh
```

The menu bar app provides:
- 🪑 **SitStraight icon** in the menu bar
- 🟢 **Real-time status** indicator (Running/Stopped)
- ⚡ **Quick start/stop** controls
- ⚙️ **Easy access** to settings and calibration
- 🔔 **System notifications** for status changes

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
python config_manager.py --camera 2  # Use camera index 2
```

## Configuration Options

| Setting | Default | Description |
|---------|---------|-------------|
| `auto_start_enabled` | `false` | Start automatically on login |
| `monitor_detection_enabled` | `true` | Pause when monitor is off |
| `alert_duration_seconds` | `4.0` | Time before first bad posture alert |
| `camera_index` | `2` | Camera device to use |
| `sitting_duration_threshold` | `1200` | Sitting time before "stand up" alert (20 min) |
| `bad_posture_duration_threshold` | `10` | Bad posture time before voice alert |
| `announcement_interval` | `10` | Seconds between continuous alerts |

## Recent Improvements

### Voice Conflict Resolution
- **Smart voice queue** prevents overlapping "sit straight" and "stand up" alerts
- **Reliable 20-minute alerts** - you'll always hear the "stand up" announcement
- **No more missed alerts** due to voice engine conflicts

### Enhanced User Experience
- **Mirrored camera view** - natural webcam-like interaction
- **20-minute sitting timer** - optimal break frequency
- **Cleaner interface** - removed unnecessary on-screen instructions
- **Improved audio system** - fresh voice engine for each alert

### Workspace Cleanup
- **Removed temporary files** and old logs
- **Streamlined codebase** with better organization
- **Updated configuration** with optimal defaults

## Troubleshooting

### Camera Issues
- Try different camera indices: `python pose_webcam.py --camera-index 1`
- Check camera permissions in System Settings
- Default camera index is 2 (UGREEN Camera 4K)

### Performance Issues
- Reduce frame rate by adjusting camera settings
- Close other applications using the camera

### Audio Issues
- Check system volume and audio output settings
- Ensure text-to-speech is enabled in macOS
- Voice alerts include both ding sound and spoken message

### Voice Alert Not Working
- The system now uses a smart voice queue to prevent conflicts
- If you don't hear alerts, check system audio settings
- Test audio with: `python test_audio.py` (if available)

## File Structure

```
sitstraight/
├── pose_webcam.py              # Main posture detection script
├── run_gui.py                  # GUI configuration interface
├── menu_bar_controller.py      # Menu bar integration
├── start_menu_bar.sh           # Menu bar launcher script
├── config_manager.py           # Command-line configuration tool
├── config.json                 # Configuration file
├── posture_calibration.json    # Personalized calibration data
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Requirements

- macOS 10.15 or later
- Python 3.10
- Webcam (UGREEN Camera 4K recommended)
- Microphone (for voice alerts)

## Usage Tips

1. **First Time Setup**: Run calibration to personalize posture detection
2. **Daily Use**: Start via menu bar for easy access
3. **Customization**: Use GUI settings to adjust timing and camera
4. **Monitoring**: Check the visual progress bar for sitting time
5. **Breaks**: Stand up when you hear the 20-minute alert

The system will help you maintain good posture and take regular breaks for better health!
 