# PosturePal - macOS Posture Detection

A smart posture detection application for macOS that uses your webcam to monitor your sitting posture and provides gentle reminders to maintain good posture.

## Features

- **Real-time Posture Detection**: Uses MediaPipe to analyze your sitting posture
- **Personalized Calibration**: Learn your good posture through a calibration process
- **Voice Alerts**: Gentle voice reminders when you slouch or sit too long
- **Menu Bar Integration**: Easy access through the macOS menu bar
- **Background Operation**: Runs quietly in the background with hidden dock icon
- **User Activity Detection**: Pauses when you're away from your computer
- **Window Controls**: Press 'h' to hide/show the detection window, 'q' to quit

## Configuration Settings

The application uses these key settings:

- **`bad_posture_duration_threshold`** (10 seconds): How long to maintain bad posture before the first alert
- **`announcement_interval`** (20 seconds): How often to repeat alerts while bad posture continues
- **`sitting_duration_threshold`** (1200 seconds = 20 minutes): How long to sit before "stand up" reminder
- **`camera_index`** (1): Which camera to use (0 for built-in, 1 for external)
- **`monitor_detection_enabled`** (true): Pause detection when monitor is off

## Quick Start

1. **Install Dependencies**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run Calibration** (first time only):
   ```bash
   python3 pose_webcam.py --calibrate --camera-index 1
   ```
   Follow the on-screen instructions to calibrate your good posture.

3. **Start the Application**:
   ```bash
   ./start.sh
   ```

## Usage

### Menu Bar Controls
- Click the menu bar icon to access controls
- Toggle posture detection on/off
- Show/hide the camera window
- Access settings and calibration

### Keyboard Controls (when window is visible)
- **'h'**: Hide/show the detection window
- **'q'**: Quit the application

### Voice Alerts
- **"Please sit up straight!"**: When bad posture is detected for 10+ seconds
- **"Stand up"**: When sitting for 20+ minutes

## Configuration

Edit `config.json` to customize settings:

```json
{
  "auto_start_enabled": true,
  "monitor_detection_enabled": true,
  "camera_index": 1,
  "sitting_duration_threshold": 1200,
  "bad_posture_duration_threshold": 10,
  "announcement_interval": 20
}
```

## Troubleshooting

### Camera Issues
- Try different camera indices (0, 1, 2)
- Ensure camera permissions are granted
- Run calibration mode to test camera access

### Menu Bar App Stops
- Check if posture detection is still running: `pgrep -f pose_webcam.py`
- Restart with: `./start.sh`

### Performance Issues
- Lower camera resolution in config
- Disable monitor detection if not needed

## Development

### Project Structure
- `pose_webcam.py`: Main posture detection logic
- `menu_bar_controller.py`: Menu bar interface
- `config_manager.py`: Configuration management
- `run_gui.py`: Settings GUI
- `launch_posture_detection.sh`: Launcher script

### Running Tests
```bash
# Test camera access
python3 pose_webcam.py --camera-index 1

# Run calibration
python3 pose_webcam.py --calibrate --camera-index 1
```

## License

MIT License - see LICENSE file for details.
 