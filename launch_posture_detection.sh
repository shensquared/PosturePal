#!/bin/bash

# Launch PosturePal with hidden dock icon
# This script ensures the Python process doesn't show in the dock

# Set environment variables to hide dock icon
export PYTHON_DISABLE_DOCK_ICON=1
export LSUIElement=1

# Activate virtual environment
source .venv/bin/activate

# Launch the posture detection with nohup to detach from terminal
nohup python pose_webcam.py --camera-index 0 > /dev/null 2>&1 &

echo "PosturePal started in background (dock icon hidden)" 