import cv2
import mediapipe as mp
import pyttsx3
import numpy as np
import time
import subprocess
import re
import sys

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

# List and display camera device names (macOS only)
if sys.platform == 'darwin':
    print("\nAvailable camera devices (from ffmpeg):")
    devices = list_mac_cameras()
    for idx, name in devices:
        print(f"  Index {idx}: {name}")
    print("(Use the index above for cam_index below)")
else:
    print("Camera device name listing is only supported on macOS in this script.")

# Always use camera index 1 (change here if needed)
cam_index = 1

# Initialize MediaPipe pose and drawing utilities
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

# Initialize voice engine
engine = pyttsx3.init()

# Open selected webcam
cap = cv2.VideoCapture(cam_index)

# Optionally, try to set a portrait resolution (may not be supported by all cameras)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 720)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1280)

# Alert logic
bad_posture_frames = 0
alert_threshold = 30  # Number of consecutive frames before alert
bad_posture_start_time = None
bad_posture_alerted = False
BAD_POSTURE_DURATION_THRESHOLD = 60  # seconds

def is_bad_pose(landmarks):
    # Slouching: shoulders much lower than hips
    left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
    right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
    left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
    right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]
    nose = landmarks[mp_pose.PoseLandmark.NOSE.value]

    avg_shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
    avg_hip_y = (left_hip.y + right_hip.y) / 2
    slouching = (avg_shoulder_y - avg_hip_y) > 0.15

    # Forward head: nose far in front of hips (x direction)
    avg_hip_x = (left_hip.x + right_hip.x) / 2
    forward_head = abs(nose.x - avg_hip_x) > 0.15  # adjust threshold as needed

    return slouching or forward_head

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

            # Check for bad posture (slouching or forward head)
            if is_bad_pose(results.pose_landmarks.landmark):
                if bad_posture_start_time is None:
                    bad_posture_start_time = time.time()
                    bad_posture_alerted = False
                bad_posture_frames += 1
                cv2.putText(image, "Bad posture detected!", (30, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                if bad_posture_frames == alert_threshold:
                    engine.say("Please sit up straight!")
                    engine.runAndWait()
                # Check if bad posture has lasted for 1 minute
                elapsed = time.time() - bad_posture_start_time
                if elapsed >= BAD_POSTURE_DURATION_THRESHOLD and not bad_posture_alerted:
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

        # Show the image (landscape)
        cv2.imshow('Pose Detection', image)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()