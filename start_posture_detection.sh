#!/bin/bash

# Posture Detection Auto-Start Script
# This script activates the virtual environment and runs the posture detection

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Log file for debugging
LOG_FILE="$SCRIPT_DIR/posture_detection.log"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Function to start the posture detection
start_posture_detection() {
    log_message "Starting posture detection..."
    
    # Activate virtual environment and run the script
    source .venv/bin/activate
    
    # Check if virtual environment is activated
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        log_message "Virtual environment activated: $VIRTUAL_ENV"
        
        # Run the posture detection script
        python pose_webcam.py --camera-index 0
        
        # Log the exit code
        EXIT_CODE=$?
        log_message "Posture detection exited with code: $EXIT_CODE"
        
        return $EXIT_CODE
    else
        log_message "ERROR: Failed to activate virtual environment"
        return 1
    fi
}

# Main loop - restart the script if it exits
log_message "Posture detection launcher started"

while true; do
    start_posture_detection
    
    # Wait a moment before restarting
    log_message "Waiting 5 seconds before restarting..."
    sleep 5
done 