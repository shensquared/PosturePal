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
    """Play a system ding sound"""
    try:
        # macOS system sound
        os.system('afplay /System/Library/Sounds/Glass.aiff')
    except:
        # Fallback: try different system sounds
        try:
            os.system('afplay /System/Library/Sounds/Ping.aiff')
        except:
            print("Could not play ding sound")

# Calibration system

class PostureCalibrator:
    def __init__(self, calibration_file="posture_calibration.json"):
        self.calibration_file = calibration_file
        self.good_examples = []
        self.bad_examples = []
        self.personalized_thresholds = {
            'slouching_threshold': 0.15,
            'forward_head_threshold': 0.15
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
                    self.personalized_thresholds = data.get('thresholds', self.personalized_thresholds)
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
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]
        nose = landmarks[mp_pose.PoseLandmark.NOSE.value]
        
        avg_shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
        avg_hip_y = (left_hip.y + right_hip.y) / 2
        avg_hip_x = (left_hip.x + right_hip.x) / 2
        
        slouching_measurement = avg_shoulder_y - avg_hip_y
        forward_head_measurement = abs(nose.x - avg_hip_x)
        
        return {
            'slouching': slouching_measurement,
            'forward_head': forward_head_measurement
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
            print(f"Added good example (slouching: {measurements['slouching']:.3f}, forward_head: {measurements['forward_head']:.3f})")
        else:
            self.bad_examples.append(example)
            print(f"Added bad example (slouching: {measurements['slouching']:.3f}, forward_head: {measurements['forward_head']:.3f})")
    
    def calculate_personalized_thresholds(self):
        """Calculate personalized thresholds from collected examples"""
        if len(self.good_examples) < 3 or len(self.bad_examples) < 3:
            print("Need at least 3 good and 3 bad examples for calibration")
            return False
        
        # Calculate statistics for good examples
        good_slouching = [ex['measurements']['slouching'] for ex in self.good_examples]
        good_forward_head = [ex['measurements']['forward_head'] for ex in self.good_examples]
        
        # Calculate statistics for bad examples
        bad_slouching = [ex['measurements']['slouching'] for ex in self.bad_examples]
        bad_forward_head = [ex['measurements']['forward_head'] for ex in self.bad_examples]
        
        # Set thresholds as midpoint between good and bad distributions
        self.personalized_thresholds['slouching_threshold'] = (
            np.mean(good_slouching) + np.mean(bad_slouching)
        ) / 2
        
        self.personalized_thresholds['forward_head_threshold'] = (
            np.mean(good_forward_head) + np.mean(bad_forward_head)
        ) / 2
        
        print(f"Personalized thresholds calculated:")
        print(f"  Slouching: {self.personalized_thresholds['slouching_threshold']:.3f}")
        print(f"  Forward head: {self.personalized_thresholds['forward_head_threshold']:.3f}")
        return True
    
    def is_bad_pose(self, landmarks, mp_pose):
        """Check if pose is bad using personalized thresholds"""
        measurements = self.calculate_measurements(landmarks, mp_pose)
        
        slouching = measurements['slouching'] > self.personalized_thresholds['slouching_threshold']
        forward_head = measurements['forward_head'] > self.personalized_thresholds['forward_head_threshold']
        
        return slouching or forward_head

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
    
    print(f"Using camera index {cam_index}")

    # Initialize MediaPipe pose and drawing utilities
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils

    # Initialize calibrator
    calibrator = PostureCalibrator()

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

    # Optionally, try to set a portrait resolution (may not be supported by all cameras)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 720)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1280)

    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

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
                cv2.putText(image, f"Slouching: {measurements['slouching']:.3f}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(image, f"Forward Head: {measurements['forward_head']:.3f}", (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # Show current thresholds
                cv2.putText(image, f"Thresholds - S: {calibrator.personalized_thresholds['slouching_threshold']:.3f}, F: {calibrator.personalized_thresholds['forward_head_threshold']:.3f}", 
                            (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                
                # Show example counts
                cv2.putText(image, f"Examples - Good: {len(calibrator.good_examples)}, Bad: {len(calibrator.bad_examples)}", 
                            (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

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

def run_normal_mode(cam_index):
    """Run the normal pose detection mode with personalized thresholds"""
    print(f"Using camera index {cam_index}")

    # Initialize MediaPipe pose and drawing utilities
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils

    # Initialize voice engine
    engine = pyttsx3.init()
    
    # Set volume and rate for better audio
    engine.setProperty('volume', 1.0)  # Maximum volume (0.0 to 1.0)
    engine.setProperty('rate', 150)     # Slightly slower for clarity

    # Initialize calibrator for personalized thresholds
    calibrator = PostureCalibrator()

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

    # Optionally, try to set a portrait resolution (may not be supported by all cameras)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 720)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1280)

    # Alert logic
    bad_posture_frames = 0
    alert_threshold = 30  # Number of consecutive frames before alert
    bad_posture_start_time = None
    bad_posture_alerted = False
    BAD_POSTURE_DURATION_THRESHOLD = 60  # seconds
    
    # Sitting timer logic
    sitting_start_time = time.time()
    sitting_alerted = False
    SITTING_DURATION_THRESHOLD = 20 * 60  # 20 minutes in seconds
    total_sitting_time = 0  # Track total actual sitting time
    last_pose_time = None  # Track when pose was last detected
    pose_detection_threshold = 3  # Seconds without pose detection to consider "not sitting"

    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

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
                print("Pose detected!")
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

                # Check for bad posture using personalized thresholds
                if calibrator.is_bad_pose(results.pose_landmarks.landmark, mp_pose):
                    if bad_posture_start_time is None:
                        bad_posture_start_time = time.time()
                        bad_posture_alerted = False
                    bad_posture_frames += 1
                    cv2.putText(image, "Bad posture detected!", (30, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    if bad_posture_frames == alert_threshold:
                        play_ding()  # Play ding sound
                        engine.say("Please sit up straight!")
                        engine.runAndWait()
                    # Check if bad posture has lasted for 1 minute
                    elapsed = time.time() - bad_posture_start_time
                    if elapsed >= BAD_POSTURE_DURATION_THRESHOLD and not bad_posture_alerted:
                        play_ding()  # Play ding sound
                        engine.say("stand up")
                        engine.runAndWait()
                        bad_posture_alerted = True
                else:
                    bad_posture_frames = 0
                    bad_posture_start_time = None
                    bad_posture_alerted = False
            else:
                bad_posture_frames = 0
                bad_posture_start_time = None
                bad_posture_alerted = False

            # Check sitting timer (only when actually sitting)
            if sitting_start_time is not None:
                sitting_elapsed = time.time() - sitting_start_time
                if sitting_elapsed >= SITTING_DURATION_THRESHOLD and not sitting_alerted:
                    play_ding()  # Play ding sound
                    engine.say("you've been sitting for 20min, take a rest")
                    engine.runAndWait()
                    sitting_alerted = True
            else:
                sitting_elapsed = 0  # Timer is paused

            # Draw sitting timer display
            draw_sitting_timer(image, sitting_elapsed, sitting_alerted)

            # Show the image (landscape)
            cv2.imshow('Pose Detection', image)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Posture detection with calibration')
    parser.add_argument('--calibrate', action='store_true', help='Run in calibration mode')
    parser.add_argument('--camera-index', type=int, default=0, help='Camera index to use (default: 0)')
    args = parser.parse_args()
    
    if args.calibrate:
        run_calibration_mode(args.camera_index)
    else:
        run_normal_mode(args.camera_index)