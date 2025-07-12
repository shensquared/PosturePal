#!/bin/bash

# Setup script for Posture Detection Auto-Start
# This script installs the launch agent to start posture detection on boot

echo "Setting up Posture Detection Auto-Start..."

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create LaunchAgents directory if it doesn't exist
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
mkdir -p "$LAUNCH_AGENTS_DIR"

# Copy the plist file to LaunchAgents and update paths
PLIST_SOURCE="$SCRIPT_DIR/com.user.posturedetection.plist"
PLIST_DEST="$LAUNCH_AGENTS_DIR/com.user.posturedetection.plist"

echo "Installing launch agent..."
cp "$PLIST_SOURCE" "$PLIST_DEST"

# Update the WorkingDirectory in the plist to use the actual script directory
echo "Updating paths in launch agent..."
sed -i.bak "s|<string>\.</string>|<string>$SCRIPT_DIR</string>|g" "$PLIST_DEST"
rm -f "$PLIST_DEST.bak"

# Load the launch agent
echo "Loading launch agent..."
launchctl load "$PLIST_DEST"

echo "✅ Posture Detection Auto-Start setup complete!"
echo ""
echo "The posture detection will now:"
echo "  • Start automatically when you log in"
echo "  • Restart automatically if it crashes or you quit it"
echo "  • Log activity to posture_detection.log"
echo ""
echo "To stop the auto-start:"
echo "  launchctl unload ~/Library/LaunchAgents/com.user.posturedetection.plist"
echo ""
echo "To start it manually:"
echo "  launchctl load ~/Library/LaunchAgents/com.user.posturedetection.plist"
echo ""
echo "To check if it's running:"
echo "  launchctl list | grep posturedetection" 