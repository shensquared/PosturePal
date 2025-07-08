import cv2
import mediapipe as mp
import pyttsx3
import numpy as np

# Initialize MediaPipe pose and drawing utilities
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

# Initialize voice engine
engine = pyttsx3.init()

# Open webcam
cap = cv2.VideoCapture(0)

# Alert logic
bad_posture_frames = 0
alert_threshold = 30  # Number of consecutive frames before alert

def is_slouching(landmarks):
    # Get y-coordinates for left/right shoulder and left/right hip
    left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
    right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
    left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
    right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]
    # Average y for shoulders and hips
    avg_shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
    avg_hip_y = (left_hip.y + right_hip.y) / 2
    # If shoulders are much lower than hips, likely slouching
    return (avg_shoulder_y - avg_hip_y) > 0.15

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
            mp_drawing.draw_landmarks(
                image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            # Check for bad posture
            if is_slouching(results.pose_landmarks.landmark):
                bad_posture_frames += 1
                cv2.putText(image, "Bad posture detected!", (30, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                if bad_posture_frames == alert_threshold:
                    engine.say("Please sit up straight!")
                    engine.runAndWait()
            else:
                bad_posture_frames = 0
        else:
            bad_posture_frames = 0

        # Show the image
        cv2.imshow('Pose Detection', image)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()