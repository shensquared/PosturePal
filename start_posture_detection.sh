#!/bin/bash

# Posture Detection Auto-Start Script with Monitor Detection
# This script activates the virtual environment and runs the posture detection
# It pauses when the monitor is off and resumes when it's on

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Log file for debugging
LOG_FILE="$SCRIPT_DIR/posture_detection.log"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Function to check if monitor is on
is_monitor_on() {
    # Use brightnessctl to check if monitor is on (brightness > 0)
    # Alternative: check if display is active using system_profiler
    if command -v brightnessctl &> /dev/null; then
        brightness=$(brightnessctl get 2>/dev/null)
        if [[ "$brightness" -gt 0 ]]; then
            return 0  # Monitor is on
        else
            return 1  # Monitor is off
        fi
    else
        # Fallback: check if display is active using system_profiler
        display_info=$(system_profiler SPDisplaysDataType 2>/dev/null | grep -i "resolution" | head -1)
        if [[ -n "$display_info" ]]; then
            return 0  # Monitor appears to be on
        else
            return 1  # Monitor appears to be off
        fi
    fi
}

# Function to wait for monitor to turn on
wait_for_monitor_on() {
    log_message "Monitor is off, waiting for it to turn on..."
    while ! is_monitor_on; do
        sleep 2
    done
    log_message "Monitor is now on, resuming posture detection..."
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

# Function to run posture detection with monitor detection
run_with_monitor_detection() {
    while true; do
        # Check if monitor is on before starting
        if is_monitor_on; then
            log_message "Monitor is on, starting posture detection..."
            start_posture_detection
            EXIT_CODE=$?
            
            # If the script exited normally (not due to monitor turning off)
            if [[ $EXIT_CODE -eq 0 ]]; then
                log_message "Posture detection exited normally"
                break
            else
                log_message "Posture detection crashed or was interrupted, restarting in 5 seconds..."
                sleep 5
            fi
        else
            # Monitor is off, wait for it to turn on
            wait_for_monitor_on
        fi
    done
}

# Main loop - restart the script if it exits
log_message "Posture detection launcher started with monitor detection"

# Initial check - wait for monitor to be on before starting
if ! is_monitor_on; then
    log_message "Monitor is currently off, waiting for it to turn on..."
    wait_for_monitor_on
fi

# Start the main loop
while true; do
    run_with_monitor_detection
    
    # If we get here, the script exited normally
    log_message "Posture detection stopped, waiting 5 seconds before checking monitor state..."
    sleep 5
done 