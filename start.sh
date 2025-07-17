#!/bin/bash

# SitStraight Menu Bar Launcher
# Provides easy access to posture detection controls from the macOS menu bar

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Log file for the menu bar app
LOG_FILE="$SCRIPT_DIR/menu_bar.log"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
    echo "$1"
}

log_message "Starting SitStraight Menu Bar..."

# Activate virtual environment
log_message "Activating virtual environment..."
source .venv/bin/activate

# Install rumps if not already installed
log_message "Checking for rumps dependency..."
python3 -c "import rumps" 2>/dev/null || {
    log_message "Installing rumps..."
    pip install rumps
}

# Start the menu bar app
log_message "Starting menu bar controller..."
PYTHON_DISABLE_DOCK_ICON=1 python3 menu_bar_controller.py

log_message "Menu bar app stopped" 