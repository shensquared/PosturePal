#!/bin/bash

# Launch PosturePal with hidden dock icon
# This script ensures the Python process doesn't show in the dock

# Set environment variables to hide dock icon
export PYTHON_DISABLE_DOCK_ICON=1
export LSUIElement=1

# Activate virtual environment
source .venv/bin/activate

# Get camera index from config file
CAMERA_INDEX=$(python3 -c "
import json
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
        print(config.get('camera_index', 0))
except:
    print(0)
")

# Launch the posture detection with nohup to detach from terminal
nohup python pose_webcam.py --camera-index $CAMERA_INDEX > /dev/null 2>&1 &

echo "PosturePal started in background (dock icon hidden)" 