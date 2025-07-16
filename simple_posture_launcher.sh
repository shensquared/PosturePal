#!/bin/bash

# Simple Posture Detection Launcher
# Runs the posture detection directly without monitor detection

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Log file for the system
LOG_FILE="$SCRIPT_DIR/simple_posture.log"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
    echo "$1"
}

log_message "Starting Simple Posture Detection..."

# Activate virtual environment and start posture detection
log_message "Activating virtual environment..."
source .venv/bin/activate

# Start the posture detection
log_message "Starting posture detection..."

# Read camera index from config file
if [ -f "config.json" ]; then
    CAMERA_INDEX=$(python3 -c "import json; print(json.load(open('config.json')).get('camera_index', 0))")
    log_message "Using camera index $CAMERA_INDEX from config.json"
else
    CAMERA_INDEX=0
    log_message "No config.json found, using default camera index 0"
fi

PYTHON_DISABLE_DOCK_ICON=1 python pose_webcam.py --camera-index $CAMERA_INDEX

log_message "Posture detection stopped" 