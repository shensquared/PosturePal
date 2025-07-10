# Posture Detection with MediaPipe

A real-time posture detection application that uses MediaPipe Pose to monitor your sitting posture and provide alerts for bad posture and extended sitting periods.

## Features

### 🎯 **Posture Detection**
- **Slouching Detection**: Monitors shoulder position relative to hips
- **Forward Head Detection**: Tracks head position relative to body
- **Personalized Calibration**: Train the system with your own posture examples

### 🔊 **Audio Alerts**
- **Voice Alerts**: "Please sit up straight!" and "stand up"
- **Ding Sounds**: Attention-grabbing system sounds
- **Sitting Timer**: "You've been sitting for 20min, take a rest" after 20 minutes

### 📊 **Visual Feedback**
- **Skeleton Overlay**: Real-time pose landmarks with body part labels
- **Measurement Display**: Shows current slouching and forward head measurements
- **Status Indicators**: Visual alerts for bad posture detection

### 🎛️ **Customization**
- **Camera Selection**: Choose any connected camera
- **Personalized Thresholds**: Calibrate based on your specific posture
- **Adjustable Alerts**: Customize timing and sensitivity

## Installation

### Prerequisites
- Python 3.7+
- macOS (for system sounds and camera access)
- Webcam or camera device

### Install Dependencies
```bash
pip install opencv-python mediapipe pyttsx3 numpy
```

### Clone and Setup
```bash
git clone <repository-url>
cd standup
python pose_webcam.py
```

## Usage

### Basic Usage
```bash
# Run with default camera (index 0)
python pose_webcam.py

# Run with specific camera
python pose_webcam.py --camera-index 2

# Run calibration mode
python pose_webcam.py --calibrate
```

### Calibration Mode
1. **Start Calibration**: `python pose_webcam.py --calibrate`
2. **Add Examples**:
   - Press `g` to add a **GOOD** posture example
   - Press `b` to add a **BAD** posture example
   - Collect at least 3 of each type
3. **Calculate Thresholds**: Press `c` to compute personalized thresholds
4. **Save Calibration**: Press `s` to save your settings
5. **Quit**: Press `q` to exit

### Normal Mode
- **Real-time Monitoring**: Automatic posture detection
- **Voice Alerts**: Audio feedback for bad posture
- **Sitting Timer**: 20-minute break reminders
- **Quit**: Press `q` to exit

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--calibrate` | Run in calibration mode | False |
| `--camera-index N` | Use camera index N | 0 |

## Camera Setup

### Finding Your Camera
The script will automatically list available cameras on macOS:
```
Available camera devices (from ffmpeg):
  Index 0: Studio Display Camera
  Index 1: UGREEN Camera 4K
  Index 2: iPhone Camera
```

### Camera Selection
```bash
# Use Studio Display Camera (default)
python pose_webcam.py

# Use UGREEN Camera
python pose_webcam.py --camera-index 1

# Use iPhone Camera
python pose_webcam.py --camera-index 2
```

## Calibration Guide

### Why Calibrate?
Personalized calibration improves accuracy by:
- Accounting for your body proportions
- Adapting to your sitting style
- Reducing false positives/negatives

### Calibration Process
1. **Good Posture Examples**: Sit in your best posture, press `g`
2. **Bad Posture Examples**: Slouch or lean forward, press `b`
3. **Threshold Calculation**: System finds optimal detection boundaries
4. **Save Settings**: Calibration data saved to `posture_calibration.json`

### Calibration Data
- **File**: `posture_calibration.json`
- **Contents**: Good/bad examples and personalized thresholds
- **Location**: Same directory as the script

## Alert System

### Posture Alerts
- **Bad Posture Detected**: After 30 consecutive frames of bad posture
- **Extended Bad Posture**: After 1 minute of continuous bad posture
- **Sitting Timer**: After 20 minutes of total sitting time

### Audio Features
- **Volume**: Maximum volume for clear alerts
- **Speech Rate**: Optimized for clarity
- **System Sounds**: macOS ding sounds for attention

## Troubleshooting

### Camera Issues
```bash
# Test available cameras
python test_camera.py

# Check camera permissions
System Preferences > Security & Privacy > Camera
```

### Common Problems

#### Camera Not Found
- Ensure camera is connected and not in use by other applications
- Check camera permissions in System Preferences
- Try different camera indices

#### No Audio Alerts
- Check system volume
- Ensure microphone permissions are granted
- Verify pyttsx3 installation

#### Poor Detection
- Ensure good lighting
- Position yourself 3-6 feet from camera
- Use plain background
- Run calibration mode for better accuracy

#### Performance Issues
- Close other applications using the camera
- Reduce camera resolution if needed
- Ensure adequate lighting

## Technical Details

### Dependencies
- **OpenCV**: Camera capture and image processing
- **MediaPipe**: Pose detection and landmark tracking
- **pyttsx3**: Text-to-speech for voice alerts
- **NumPy**: Numerical computations

### Pose Detection
- **Model**: MediaPipe Pose (BlazePose)
- **Landmarks**: 33 body points
- **Confidence**: 0.5 minimum detection/tracking confidence

### Measurements
- **Slouching**: Shoulder-to-hip vertical distance
- **Forward Head**: Head-to-hip horizontal distance
- **Thresholds**: Personalized based on calibration data

## File Structure
```
standup/
├── pose_webcam.py          # Main application
├── test_camera.py          # Camera testing utility
├── posture_calibration.json # Calibration data (auto-generated)
└── README.md              # This file
```

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve the application.

## Acknowledgments

- **MediaPipe**: Google's pose detection technology
- **OpenCV**: Computer vision library
- **pyttsx3**: Text-to-speech functionality 