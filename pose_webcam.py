import cv2
import mediapipe as mp
import pyttsx3
import numpy as np
import time
import subprocess
import re
import sys
import argparse
import json
import os

# Configuration
CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "auto_start_enabled": False,
    "monitor_detection_enabled": False,
    "alert_duration_seconds": 5.0,
    "camera_index": 0,
    "sitting_duration_threshold": 1800,
    "bad_posture_duration_threshold": 60,
    "announcement_interval": 5,
    "camera_width": 640,  # Lower resolution for better performance
    "camera_height": 480,  # Lower resolution for better performance
    "processing_fps": 10   # Process every Nth frame instead of every frame
}

def is_user_active():
    """Check if the user is currently active (not idle)"""
    try:
        # Use IOHIDSystem to get user idle time on macOS
        result = subprocess.run(['ioreg', '-c', 'IOHIDSystem'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if 'HIDIdleTime' in line:
                    # Extract the idle time value (in nanoseconds)
                    import re
                    match = re.search(r'HIDIdleTime\s*=\s*(\d+)', line)
                    if match:
                        idle_time_ns = int(match.group(1))
                        idle_time_seconds = idle_time_ns / 1_000_000_000  # Convert to seconds
                        
                        # Consider user inactive if idle for more than 2 minutes (120 seconds)
                        return idle_time_seconds < 120
        return True  # Default to True if we can't determine
    except Exception as e:
        print(f"User activity detection error: {e}")
        return True  # Default to True on error

def load_config():
    """Load configuration from file"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # Merge with defaults to ensure all keys exist
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception as e:
            print(f"Error loading config: {e}")
            return DEFAULT_CONFIG.copy()
    else:
        return DEFAULT_CONFIG.copy()

# Helper to list camera device names on macOS using ffmpeg

def list_mac_cameras():
    try:
        result = subprocess.run(
            ['ffmpeg', '-f', 'avfoundation', '-list_devices', 'true', '-i', '""'],
            stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True
        )
        devices = []
        for line in result.stderr.splitlines():
            m = re.search(r'\[(\d+)\] (.+)', line)
            if m:
                idx, name = m.groups()
                devices.append((int(idx), name.strip()))
        return devices
    except Exception as e:
        print(f"Could not list camera devices: {e}")
        return []

# Helper to play a ding sound
def play_ding():
    """Play a system ding sound for posture alerts"""
    try:
        # macOS system sound
        os.system('afplay /System/Library/Sounds/Glass.aiff')
    except Exception as e:
        # Fallback: try different system sounds
        try:
            os.system('afplay /System/Library/Sounds/Ping.aiff')
        except Exception as e2:
            print(f"Could not play ding sound: {e}, {e2}")

def play_stand_up_sound():
    """Play Hero sound three times for stand up alerts"""
    try:
        # Play Hero sound three times with short pauses
        for i in range(3):
            os.system('afplay /System/Library/Sounds/Hero.aiff')
            if i < 2:  # Don't sleep after the last one
                time.sleep(0.3)  # Short pause between sounds
    except Exception as e:
        # Fallback: try different system sounds
        try:
            for i in range(3):
                os.system('afplay /System/Library/Sounds/Basso.aiff')
                if i < 2:
                    time.sleep(0.3)
        except Exception as e2:
            try:
                for i in range(3):
                    os.system('afplay /System/Library/Sounds/Sosumi.aiff')
                    if i < 2:
                        time.sleep(0.3)
            except Exception as e3:
                print(f"Could not play stand up sound: {e}, {e2}, {e3}")
                # Final fallback to regular ding
                play_ding()

def toggle_camera_window(window_should_be_visible, window_created):
    """Toggle camera window visibility"""
    try:
        # Toggle the visibility flag
        window_should_be_visible = not window_should_be_visible
        
        if window_should_be_visible:
            # Create window if it doesn't exist
            if not window_created:
                cv2.namedWindow('Pose Detection', cv2.WINDOW_NORMAL)
                cv2.setWindowProperty('Pose Detection', cv2.WND_PROP_TOPMOST, 1)
                cv2.resizeWindow('Pose Detection', 800, 600)
                # Set window title with more descriptive name (if supported)
                try:
                    cv2.setWindowProperty('Pose Detection', cv2.WND_PROP_TITLE, 'SitStraight - Posture Detection')
                except AttributeError:
                    # WND_PROP_TITLE not available in this OpenCV version, skip it
                    pass
                
                # Additional macOS-specific dock hiding when window is created
                if sys.platform == 'darwin':
                    try:
                        import AppKit
                        # Re-hide dock icon after window creation
                        app = AppKit.NSApplication.sharedApplication()
                        app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)
                    except ImportError:
                        pass
                
                window_created = True
            
            # Show window
            cv2.setWindowProperty('Pose Detection', cv2.WND_PROP_VISIBLE, 1)
            if sys.platform == 'darwin':
                cv2.moveWindow('Pose Detection', 100, 100)
                
                # Additional dock hiding after showing window
                try:
                    import AppKit
                    app = AppKit.NSApplication.sharedApplication()
                    app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)
                except ImportError:
                    pass
        else:
            # Hide window
            if window_created:
                cv2.setWindowProperty('Pose Detection', cv2.WND_PROP_VISIBLE, 0)
                if sys.platform == 'darwin':
                    cv2.moveWindow('Pose Detection', 3000, 3000)
        
        return window_should_be_visible, window_created
    except Exception as e:
        print(f"DEBUG: Error toggling window: {e}")
        return window_should_be_visible, window_created

def update_status_file(status_file, sitting_start_time, sitting_elapsed, window_visible=True):
    """Update status file with current posture detection state"""
    try:
        status = {
            "timestamp": time.time(),
            "sitting_start_time": sitting_start_time,
            "sitting_elapsed": sitting_elapsed,
            "window_visible": window_visible,
            "is_sitting": sitting_start_time is not None
        }
        
        with open(status_file, 'w') as f:
            json.dump(status, f)
    except Exception as e:
        print(f"Error updating status file: {e}")

def safe_speak(engine, message, voice_busy, last_voice_time, sound_type="posture"):
    """Safely speak a message, avoiding conflicts with other voice announcements"""
    current_time = time.time()
    
    # If voice is busy or too soon after last announcement, skip this one
    if voice_busy or (current_time - last_voice_time) < 2.0:
        return voice_busy, last_voice_time
    
    try:
        voice_busy = True
        # Play different sounds based on alert type
        if sound_type == "stand_up":
            play_stand_up_sound()  # Play stand up sound
        else:
            play_ding()  # Play regular ding sound for posture alerts
        engine.say(message)
        engine.runAndWait()
        time.sleep(0.5)  # Short pause to ensure audio plays
        last_voice_time = current_time
        voice_busy = False
        return voice_busy, last_voice_time
    except Exception as e:
        print(f"Voice alert error: {e}")
        voice_busy = False
        return voice_busy, last_voice_time

# Calibration system

class PostureCalibrator:
    def __init__(self, calibration_file="posture_calibration.json"):
        self.calibration_file = calibration_file
        self.good_examples = []
        self.bad_examples = []
        self.personalized_thresholds = {
            'head_height_threshold': 0.1,
            'nose_height_threshold': 0.7  # Nose should be in upper 30% of frame for good posture
        }
        self.load_calibration()
    
    def load_calibration(self):
        """Load existing calibration data"""
        if os.path.exists(self.calibration_file):
            try:
                with open(self.calibration_file, 'r') as f:
                    data = json.load(f)
                    self.good_examples = data.get('good_examples', [])
                    self.bad_examples = data.get('bad_examples', [])
                    loaded_thresholds = data.get('thresholds', {})
                    
                    # Merge with defaults to ensure all required thresholds exist
                    for key, value in self.personalized_thresholds.items():
                        if key not in loaded_thresholds:
                            loaded_thresholds[key] = value
                    
                    self.personalized_thresholds = loaded_thresholds
                print(f"Loaded calibration data: {len(self.good_examples)} good, {len(self.bad_examples)} bad examples")
            except Exception as e:
                print(f"Error loading calibration: {e}")
    
    def save_calibration(self):
        """Save calibration data"""
        data = {
            'good_examples': self.good_examples,
            'bad_examples': self.bad_examples,
            'thresholds': self.personalized_thresholds
        }
        try:
            with open(self.calibration_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Calibration saved to {self.calibration_file}")
        except Exception as e:
            print(f"Error saving calibration: {e}")
    
    def calculate_measurements(self, landmarks, mp_pose):
        """Calculate posture measurements from landmarks"""
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        nose = landmarks[mp_pose.PoseLandmark.NOSE.value]
        
        avg_shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
        
        # Head height: vertical distance from shoulders to nose
        head_height_measurement = avg_shoulder_y - nose.y  # Positive when head is above shoulders
        # Nose height in frame: relative position from top of frame (0 = top, 1 = bottom)
        nose_height_in_frame = nose.y  # MediaPipe y-coordinate is 0 at top, 1 at bottom
        
        return {
            'head_height': head_height_measurement,
            'nose_height_in_frame': nose_height_in_frame
        }
    
    def add_example(self, landmarks, is_good, mp_pose):
        """Add a posture example"""
        measurements = self.calculate_measurements(landmarks, mp_pose)
        example = {
            'measurements': measurements,
            'timestamp': time.time()
        }
        
        if is_good:
            self.good_examples.append(example)
            print(f"Added good example (head_height: {measurements['head_height']:.3f}, nose_height: {measurements['nose_height_in_frame']:.3f})")
        else:
            self.bad_examples.append(example)
            print(f"Added bad example (head_height: {measurements['head_height']:.3f}, nose_height: {measurements['nose_height_in_frame']:.3f})")
    
    def calculate_personalized_thresholds(self):
        """Calculate personalized thresholds from collected examples"""
        if len(self.good_examples) < 3 or len(self.bad_examples) < 3:
            print("Need at least 3 good and 3 bad examples for calibration")
            return False
        
        # Calculate statistics for good examples
        good_head_height = [ex['measurements']['head_height'] for ex in self.good_examples]
        good_nose_height = [ex['measurements']['nose_height_in_frame'] for ex in self.good_examples]
        
        # Calculate statistics for bad examples
        bad_head_height = [ex['measurements']['head_height'] for ex in self.bad_examples]
        bad_nose_height = [ex['measurements']['nose_height_in_frame'] for ex in self.bad_examples]
        
        # Set thresholds as midpoint between good and bad distributions
        self.personalized_thresholds['head_height_threshold'] = (
            np.mean(good_head_height) + np.mean(bad_head_height)
        ) / 2
        
        self.personalized_thresholds['nose_height_threshold'] = (
            np.mean(good_nose_height) + np.mean(bad_nose_height)
        ) / 2
        
        print(f"Personalized thresholds calculated:")
        print(f"  Head height: {self.personalized_thresholds['head_height_threshold']:.3f}")
        print(f"  Nose height: {self.personalized_thresholds['nose_height_threshold']:.3f}")
        return True
    
    def is_bad_pose(self, landmarks, mp_pose):
        """Check if pose is bad using personalized thresholds"""
        measurements = self.calculate_measurements(landmarks, mp_pose)
        
        head_height_bad = measurements['head_height'] < self.personalized_thresholds['head_height_threshold']
        nose_height_bad = measurements['nose_height_in_frame'] > self.personalized_thresholds['nose_height_threshold']
        
        return head_height_bad or nose_height_bad

def run_calibration_mode(cam_index):
    """Run the calibration mode to collect posture examples"""
    print("=== POSTURE CALIBRATION MODE ===")
    print("Instructions:")
    print("1. Press 'g' to add a GOOD posture example")
    print("2. Press 'b' to add a BAD posture example")
    print("3. Press 'c' to calculate personalized thresholds")
    print("4. Press 's' to save calibration")
    print("5. Press 'q' to quit")
    print()
    
    # List available cameras on macOS
    print("Available cameras:")
    cameras = list_mac_cameras()
    if cameras:
        for idx, name in cameras:
            print(f"  [{idx}] {name}")
    else:
        print("  Could not detect cameras automatically")
    print()
    
    print(f"Using camera index {cam_index}")

    # Initialize MediaPipe pose and drawing utilities
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils

    # Initialize calibrator
    calibrator = PostureCalibrator()
    
    # Debug: Print loaded thresholds
    print(f"DEBUG: Loaded thresholds - Head height: {calibrator.personalized_thresholds['head_height_threshold']:.3f}, Nose height: {calibrator.personalized_thresholds['nose_height_threshold']:.3f}")

    # Open selected webcam
    print(f"Attempting to open camera at index {cam_index}...")
    cap = cv2.VideoCapture(cam_index)
    
    # Verify camera opened successfully
    if not cap.isOpened():
        print(f"Failed to open camera at index {cam_index}")
        print("Trying to open camera at index 0...")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Failed to open any camera. Exiting.")
            return
    
    # Verify the camera is actually working by reading a test frame
    ret, test_frame = cap.read()
    if not ret or test_frame is None:
        print(f"Camera at index {cam_index} opened but cannot read frames")
        print("Trying to open camera at index 0...")
        cap.release()
        cap = cv2.VideoCapture(0)
        ret, test_frame = cap.read()
        if not ret or test_frame is None:
            print("Failed to open any working camera. Exiting.")
            return
    
    # Get camera info to verify
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    print(f"Camera opened successfully: {width}x{height}")

    # Set lower resolution for better performance
    config = load_config()
    target_width = config.get('camera_width', 640)
    target_height = config.get('camera_height', 480)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, target_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, target_height)

    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Flip the frame horizontally (mirror effect)
            frame = cv2.flip(frame, 1)

            # Convert the BGR image to RGB
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False

            # Make pose detection
            results = pose.process(image)

            # Draw pose landmarks on the image
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            if results.pose_landmarks:
                # Draw pose landmarks and connections
                mp_drawing.draw_landmarks(
                    image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

                # Annotate each skeleton line with body part names
                landmark_points = results.pose_landmarks.landmark
                h, w = image.shape[:2]
                for connection in mp_pose.POSE_CONNECTIONS:
                    start_idx, end_idx = connection
                    start_lm = landmark_points[start_idx]
                    end_lm = landmark_points[end_idx]
                    # Get pixel coordinates
                    start_xy = (int(start_lm.x * w), int(start_lm.y * h))
                    end_xy = (int(end_lm.x * w), int(end_lm.y * h))
                    # Get landmark names
                    start_name = mp_pose.PoseLandmark(start_idx).name.replace("_", " ").title()
                    end_name = mp_pose.PoseLandmark(end_idx).name.replace("_", " ").title()
                    # Draw text near each endpoint
                    cv2.putText(image, start_name, (start_xy[0]+5, start_xy[1]-5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1, cv2.LINE_AA)
                    cv2.putText(image, end_name, (end_xy[0]+5, end_xy[1]-5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1, cv2.LINE_AA)

                # Show current measurements
                measurements = calibrator.calculate_measurements(results.pose_landmarks.landmark, mp_pose)
                cv2.putText(image, f"Head Height: {measurements['head_height']:.3f}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(image, f"Nose Height: {measurements['nose_height_in_frame']:.3f}", (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                # Show current thresholds (always from calibrator.personalized_thresholds)
                cv2.putText(
                    image,
                    f"Thresholds: H={calibrator.personalized_thresholds['head_height_threshold']:.3f}, N={calibrator.personalized_thresholds['nose_height_threshold']:.3f}",
                    (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                
                # Show example counts
                cv2.putText(image, f"Examples - Good: {len(calibrator.good_examples)}, Bad: {len(calibrator.bad_examples)}", 
                            (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

            # Show the image (landscape)
            cv2.imshow('Posture Calibration', image)
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                break
            elif key == ord('g') and results.pose_landmarks:
                calibrator.add_example(results.pose_landmarks.landmark, True, mp_pose)
            elif key == ord('b') and results.pose_landmarks:
                calibrator.add_example(results.pose_landmarks.landmark, False, mp_pose)
            elif key == ord('c'):
                if calibrator.calculate_personalized_thresholds():
                    print("Personalized thresholds calculated successfully!")
                else:
                    print("Not enough examples for calibration")
            elif key == ord('s'):
                calibrator.save_calibration()

    cap.release()
    cv2.destroyAllWindows()

def draw_sitting_timer(image, elapsed_time, alerted):
    """Draw a visual timelapse-style sitting timer on the image"""
    # Convert elapsed time to hours, minutes, seconds
    hours = int(elapsed_time // 3600)
    minutes = int((elapsed_time % 3600) // 60)
    seconds = int(elapsed_time % 60)
    
    # Format time string
    if hours > 0:
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        time_str = f"{minutes:02d}:{seconds:02d}"
    
    # Get image dimensions
    h, w = image.shape[:2]
    
    # Timer position (top-right corner)
    timer_x = w - 200
    timer_y = 50
    
    # Background rectangle for timer
    bg_color = (0, 0, 0) if not alerted else (0, 0, 255)  # Red background if alerted
    cv2.rectangle(image, (timer_x - 10, timer_y - 30), (timer_x + 190, timer_y + 10), bg_color, -1)
    cv2.rectangle(image, (timer_x - 10, timer_y - 30), (timer_x + 190, timer_y + 10), (255, 255, 255), 2)
    
    # Timer text
    text_color = (255, 255, 255) if not alerted else (255, 255, 255)
    if elapsed_time == 0:
        cv2.putText(image, "Sitting: PAUSED", (timer_x, timer_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (128, 128, 128), 2)
    else:
        cv2.putText(image, f"Sitting: {time_str}", (timer_x, timer_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 2)
    
    # Progress bar (timelapse style)
    bar_width = 180
    bar_height = 8
    bar_x = timer_x
    bar_y = timer_y + 20
    
    # Calculate progress (20 minutes = 100%)
    progress = min(elapsed_time / (20 * 60), 1.0)  # 20 minutes max
    filled_width = int(bar_width * progress)
    
    # Draw progress bar background
    cv2.rectangle(image, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (100, 100, 100), -1)
    
    # Draw filled progress
    if progress > 0:
        # Color gradient: green -> yellow -> red
        if progress < 0.5:
            # Green to yellow
            color_ratio = progress / 0.5
            color = (0, int(255 * (1 - color_ratio)), int(255 * color_ratio))
        else:
            # Yellow to red
            color_ratio = (progress - 0.5) / 0.5
            color = (0, int(255 * (1 - color_ratio)), 255)
        
        cv2.rectangle(image, (bar_x, bar_y), (bar_x + filled_width, bar_y + bar_height), color, -1)
    
    # Progress bar border
    cv2.rectangle(image, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (255, 255, 255), 1)
    
    # Add percentage text
    percentage = int(progress * 100)
    cv2.putText(image, f"{percentage}%", (bar_x + bar_width + 10, bar_y + bar_height + 5), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Add warning text if sitting too long
    if alerted:
        cv2.putText(image, "TAKE A BREAK!", (timer_x, timer_y + 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

def draw_posture_metrics(image, measurements, thresholds, bad_reasons=None):
    """Draw posture metrics on the image"""
    # Get image dimensions
    h, w = image.shape[:2]
    
    # Metrics position (bottom-left corner, above quit instruction)
    metrics_x = 10
    metrics_y = h - 120  # Moved back up since we removed one metric
    
    # Calculate text size to determine background rectangle size
    font_scale = 0.4
    font_thickness = 1
    line_height = 18
    
    # Draw metrics without background rectangle for less visual interference
    y_offset = 0
    
    # Head height measurement
    head_height_status = "❌" if measurements['head_height'] < thresholds['head_height_threshold'] else "✅"
    head_height_color = (0, 0, 255) if measurements['head_height'] < thresholds['head_height_threshold'] else (0, 255, 0)
    cv2.putText(image, f"{head_height_status} Height: {measurements['head_height']:.3f} (>{thresholds['head_height_threshold']:.3f})", 
                (metrics_x, metrics_y + y_offset), cv2.FONT_HERSHEY_SIMPLEX, font_scale, head_height_color, font_thickness)
    y_offset += line_height
    
    # Nose height in frame measurement (now used for alerts)
    nose_height_status = "❌" if measurements['nose_height_in_frame'] > thresholds['nose_height_threshold'] else "✅"
    nose_height_color = (0, 0, 255) if measurements['nose_height_in_frame'] > thresholds['nose_height_threshold'] else (0, 255, 0)
    cv2.putText(image, f"{nose_height_status} Nose Y: {measurements['nose_height_in_frame']:.3f} (<{thresholds['nose_height_threshold']:.3f})", 
                (metrics_x, metrics_y + y_offset), cv2.FONT_HERSHEY_SIMPLEX, font_scale, nose_height_color, font_thickness)
    y_offset += line_height
    # Show thresholds below the metrics
    cv2.putText(
        image,
        f"Thresholds: H={thresholds['head_height_threshold']:.3f}, N={thresholds['nose_height_threshold']:.3f}",
        (metrics_x, metrics_y + y_offset),
        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
    
    # Draw bad posture warning if any (smaller and more subtle)
    if bad_reasons:
        y_offset += line_height + 5
        cv2.putText(image, f"⚠️ BAD POSTURE", (metrics_x, metrics_y + y_offset), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

def run_normal_mode(cam_index):
    """Run the normal pose detection mode with personalized thresholds"""
    # Load configuration
    config = load_config()
    
    # List available cameras on macOS
    print("Available cameras:")
    cameras = list_mac_cameras()
    if cameras:
        for idx, name in cameras:
            print(f"  [{idx}] {name}")
    else:
        print("  Could not detect cameras automatically")
    print()
    
    print(f"Using camera index {cam_index}")
    print(f"Configuration loaded:")
    print(f"  Alert duration: {config['alert_duration_seconds']} seconds")
    print(f"  Monitor detection: {'Enabled' if config['monitor_detection_enabled'] else 'Disabled'}")
    print(f"  Sitting threshold: {config['sitting_duration_threshold']} seconds")
    print(f"  Bad posture threshold: {config['bad_posture_duration_threshold']} seconds")

    # Initialize MediaPipe pose and drawing utilities
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils

    # Initialize voice engine
    engine = pyttsx3.init()
    
    # Set volume and rate for better audio
    engine.setProperty('volume', 1.0)  # Maximum volume (0.0 to 1.0)
    engine.setProperty('rate', 150)     # Slightly slower for clarity
    
    # Voice queue to prevent conflicts
    voice_busy = False
    last_voice_time = 0

    # Initialize calibrator for personalized thresholds
    calibrator = PostureCalibrator()
    
    # Debug: Print loaded thresholds
    print(f"DEBUG: Loaded thresholds - Head height: {calibrator.personalized_thresholds['head_height_threshold']:.3f}, Nose height: {calibrator.personalized_thresholds['nose_height_threshold']:.3f}")

    # Open selected webcam
    print(f"Attempting to open camera at index {cam_index}...")
    cap = cv2.VideoCapture(cam_index)
    
    # Verify camera opened successfully
    if not cap.isOpened():
        print(f"Failed to open camera at index {cam_index}")
        print("Trying to open camera at index 0...")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Failed to open any camera. Exiting.")
            return
    
    # Get camera info to verify
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    print(f"Camera opened successfully: {width}x{height}")

    # Set lower resolution for better performance
    target_width = config.get('camera_width', 640)
    target_height = config.get('camera_height', 480)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, target_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, target_height)

    # Get actual frame rate
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        # If FPS is not available, estimate it
        print("FPS not available from camera, estimating...")
        start_time = time.time()
        for _ in range(30):  # Sample 30 frames
            ret, _ = cap.read()
            if not ret:
                break
        end_time = time.time()
        fps = 30 / (end_time - start_time) if (end_time - start_time) > 0 else 30
    
    print(f"Camera frame rate: {fps:.1f} FPS")
    
    # Calculate alert threshold based on frame rate and configuration
    alert_threshold = max(1, int(fps * config['alert_duration_seconds']))
    print(f"Alert threshold set to {alert_threshold} frames ({alert_threshold/fps:.1f} seconds)")

    # Alert logic
    bad_posture_frames = 0
    bad_posture_start_time = None
    bad_posture_alerted = False
    BAD_POSTURE_DURATION_THRESHOLD = config['bad_posture_duration_threshold']  # seconds
    last_announcement_time = 0
    ANNOUNCEMENT_INTERVAL = config['announcement_interval']  # Announce every N seconds when bad posture continues
    
    # Sitting timer logic
    sitting_start_time = None  # Will be set when pose is first detected
    sitting_alerted = False
    SITTING_DURATION_THRESHOLD = config['sitting_duration_threshold']  # seconds
    total_sitting_time = 0  # Track total actual sitting time
    last_pose_time = None  # Track when pose was last detected
    pose_detection_threshold = 3  # Seconds without pose detection to consider "not sitting"
    
    # Status file for communication with menu bar
    status_file = "posture_status.json"
    
    # Window visibility control
    window_should_be_visible = False
    window_created = False
    
    # Frame counter for periodic tasks
    frame_count = 0

    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        # Don't create the window initially - create it only when needed
        
        # Additional macOS-specific dock hiding for OpenCV window
        if sys.platform == 'darwin':
            try:
                import AppKit
                # Hide dock icon for the OpenCV window
                AppKit.NSApplication.sharedApplication()
                AppKit.NSApp.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)
            except ImportError:
                # AppKit not available, use alternative method
                pass
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1

            # Check user activity if monitor detection is enabled
            if config['monitor_detection_enabled']:
                user_active = is_user_active()
                if not user_active:
                    # User is idle - pause detection
                    time.sleep(1)  # Sleep for 1 second before checking again
                    continue  # Skip this frame and continue loop

            # Flip the frame horizontally (mirror effect)
            frame = cv2.flip(frame, 1)

            # Convert the BGR image to RGB
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False

            # Make pose detection
            results = pose.process(image)
            
            # Update sitting timer based on pose detection
            current_time = time.time()
            if results.pose_landmarks:
                # Pose detected - update last pose time
                last_pose_time = current_time
                # If this is the first pose detection after being away, resume timer
                if sitting_start_time is None:
                    sitting_start_time = current_time
                    debug_msg = f"DEBUG: Sitting timer started at {time.strftime('%H:%M:%S')}"
                    print(debug_msg)
                    try:
                        with open('simple_posture.log', 'a') as f:
                            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {debug_msg}\n")
                    except:
                        pass
            else:
                # No pose detected - check if we should pause timer
                if last_pose_time and (current_time - last_pose_time) > pose_detection_threshold:
                    # Been away for more than threshold - pause timer
                    if sitting_start_time is not None:
                        sitting_start_time = None  # Pause timer

            # Draw pose landmarks on the image
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            if results.pose_landmarks:
                # Calculate measurements for posture detection
                measurements = calibrator.calculate_measurements(results.pose_landmarks.landmark, mp_pose)
                # Draw only the key points used for posture calculation
                landmark_points = results.pose_landmarks.landmark
                h, w = image.shape[:2]
                
                # Draw key landmarks: shoulders, nose
                key_landmarks = [
                    mp_pose.PoseLandmark.LEFT_SHOULDER,
                    mp_pose.PoseLandmark.RIGHT_SHOULDER,
                    mp_pose.PoseLandmark.NOSE
                ]
                
                for landmark in key_landmarks:
                    lm = landmark_points[landmark.value]
                    x, y = int(lm.x * w), int(lm.y * h)
                    # Draw circle for each key point
                    cv2.circle(image, (x, y), 8, (0, 255, 0), -1)  # Green circles
                    # Draw landmark name
                    name = landmark.name.replace("_", " ").title()
                    cv2.putText(image, name, (x+10, y-10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
                
                # Draw line connecting shoulders for visual reference
                left_shoulder = landmark_points[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
                right_shoulder = landmark_points[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
                
                # Shoulder line
                cv2.line(image, 
                        (int(left_shoulder.x * w), int(left_shoulder.y * h)),
                        (int(right_shoulder.x * w), int(right_shoulder.y * h)),
                        (255, 255, 0), 2)  # Yellow line

                # Check for bad posture using personalized thresholds
                measurements = calibrator.calculate_measurements(results.pose_landmarks.landmark, mp_pose)
                bad_reasons = []
                
                if measurements['head_height'] < calibrator.personalized_thresholds['head_height_threshold']:
                    bad_reasons.append("head height")
                if measurements['nose_height_in_frame'] > calibrator.personalized_thresholds['nose_height_threshold']:
                    bad_reasons.append("nose too low")
                
                if bad_reasons:
                    if bad_posture_start_time is None:
                        bad_posture_start_time = time.time()
                        bad_posture_alerted = False
                        last_announcement_time = 0
                        debug_msg = f"DEBUG: Bad posture detected: {bad_reasons}"
                        print(debug_msg)
                        # Also write to log file
                        try:
                            with open('simple_posture.log', 'a') as f:
                                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {debug_msg}\n")
                        except:
                            pass
                    bad_posture_frames += 1
                    
                    cv2.putText(image, f"Bad posture: {', '.join(bad_reasons)}", (30, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    
                    current_time = time.time()
                    elapsed = current_time - bad_posture_start_time
                    
                    # Initial alert after bad posture duration threshold
                    if elapsed >= BAD_POSTURE_DURATION_THRESHOLD and last_announcement_time == 0:
                        debug_msg = f"DEBUG: Bad posture alert triggered after {elapsed:.1f} seconds (threshold: {BAD_POSTURE_DURATION_THRESHOLD})"
                        print(debug_msg)
                        # Also write to log file
                        try:
                            with open('simple_posture.log', 'a') as f:
                                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {debug_msg}\n")
                        except:
                            pass
                        voice_busy, last_voice_time = safe_speak(engine, "Please sit up straight!", voice_busy, last_voice_time)
                        last_announcement_time = current_time
                    
                    # Continuous announcements every ANNOUNCEMENT_INTERVAL seconds (only after initial alert)
                    elif last_announcement_time > 0 and (current_time - last_announcement_time) >= ANNOUNCEMENT_INTERVAL:
                        debug_msg = f"DEBUG: Continuous alert triggered after {current_time - last_announcement_time:.1f} seconds"
                        print(debug_msg)
                        try:
                            with open('simple_posture.log', 'a') as f:
                                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {debug_msg}\n")
                        except:
                            pass
                        voice_busy, last_voice_time = safe_speak(engine, "Please sit up straight!", voice_busy, last_voice_time)
                        last_announcement_time = current_time
                    
                    # Note: "stand up" announcement moved to sitting timer section
                else:
                    bad_posture_frames = 0
                    bad_posture_start_time = None
                    bad_posture_alerted = False
            else:
                # No pose detected - reset all bad posture tracking
                bad_posture_frames = 0
                bad_posture_start_time = None
                bad_posture_alerted = False
                last_announcement_time = 0  # Reset announcement timer as well
                
                # Only reset sitting alert if person has been away for a long time (more than 30 seconds)
                # This prevents resetting the alert due to brief pose detection failures
                if last_pose_time and (current_time - last_pose_time) > 30:
                    sitting_alerted = False
                    debug_msg = f"DEBUG: Sitting alert reset after being away for {current_time - last_pose_time:.1f} seconds"
                    print(debug_msg)
                    try:
                        with open('simple_posture.log', 'a') as f:
                            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {debug_msg}\n")
                    except:
                        pass

            # Check sitting timer (only when actually sitting)
            if sitting_start_time is not None:
                sitting_elapsed = time.time() - sitting_start_time
                if sitting_elapsed >= SITTING_DURATION_THRESHOLD and not sitting_alerted:
                    debug_msg = f"DEBUG: Stand up alert triggered after {sitting_elapsed:.1f} seconds (threshold: {SITTING_DURATION_THRESHOLD})"
                    print(debug_msg)
                    try:
                        with open('simple_posture.log', 'a') as f:
                            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {debug_msg}\n")
                    except:
                        pass
                    voice_busy, last_voice_time = safe_speak(engine, "stand up", voice_busy, last_voice_time, "stand_up")
                    sitting_alerted = True
            else:
                sitting_elapsed = 0  # Timer is paused
            
            # Check for window toggle request from menu bar
            try:
                if os.path.exists("toggle_window.txt"):
                    window_should_be_visible, window_created = toggle_camera_window(window_should_be_visible, window_created)
                    os.remove("toggle_window.txt")
            except:
                pass
            
            # Update status file for menu bar communication
            try:
                update_status_file(status_file, sitting_start_time, sitting_elapsed, window_should_be_visible)
            except Exception as e:
                print(f"DEBUG: Error updating status: {e}")
            
            # Periodic dock icon hiding check (every 30 frames, roughly every second)
            if frame_count % 30 == 0 and sys.platform == 'darwin':
                try:
                    import AppKit
                    app = AppKit.NSApplication.sharedApplication()
                    app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)
                except ImportError:
                    pass

            # Draw posture metrics if pose is detected
            if results.pose_landmarks:
                draw_posture_metrics(image, measurements, calibrator.personalized_thresholds, bad_reasons if 'bad_reasons' in locals() else None)

            # Draw sitting timer display
            draw_sitting_timer(image, sitting_elapsed, sitting_alerted)

            # Remove the 'Press q to quit' instruction
            # h, w = image.shape[:2]
            # cv2.putText(image, "Press 'q' to quit", (10, h - 20), 
            #             cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Show the image (landscape) - only if window should be visible
            if window_should_be_visible and window_created:
                cv2.imshow('Pose Detection', image)
            else:
                # Still need to process events even when window is hidden
                cv2.waitKey(1)
            
            # Check for quit key (q) or window close
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("Quit requested by user (keyboard)")
                break
            
            # Note: Window visibility is controlled by the menu bar toggle system
            # We don't check window visibility here to avoid quitting when window is minimized
            


        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    # Hide dock icon for posture detection on macOS
    import os
    import sys
    
    # Set environment variable to hide dock icon
    os.environ['PYTHON_DISABLE_DOCK_ICON'] = '1'
    
    # Additional macOS-specific dock hiding
    if sys.platform == 'darwin':
        try:
            import AppKit
            # Hide dock icon - multiple methods for better compatibility
            app = AppKit.NSApplication.sharedApplication()
            app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)
            
            # Additional method to ensure dock icon is hidden
            try:
                import Foundation
                # Set LSUIElement to true in Info.plist equivalent
                Foundation.NSBundle.mainBundle().infoDictionary()['LSUIElement'] = True
            except:
                pass
                
        except ImportError:
            # AppKit not available, try alternative method
            try:
                # Set environment variable that some Python distributions recognize
                os.environ['LSUIElement'] = '1'
            except:
                pass
    
    parser = argparse.ArgumentParser(description='Posture detection with calibration')
    parser.add_argument('--calibrate', action='store_true', help='Run in calibration mode')
    parser.add_argument('--camera-index', type=int, default=0, help='Camera index to use (default: 0)')
    args = parser.parse_args()
    
    if args.calibrate:
        run_calibration_mode(args.camera_index)
    else:
        run_normal_mode(args.camera_index)