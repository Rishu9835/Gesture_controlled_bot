import cv2
import mediapipe as mp
import requests
import numpy as np
import math

#CONFIGURE
ESP32_STREAM_URL = "http://<esp-ip>:81"
ESP32_CMD_URL = "http://<esp-ip>/move?cmd="

#Setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

last_cmd = ""
last_speed = -1

def send_command(cmd, speed=None):
    global last_cmd, last_speed
    full_cmd = cmd
    if speed is not None:
        full_cmd += str(speed)

    if full_cmd != last_cmd:
        try:
            requests.get(ESP32_CMD_URL + full_cmd, timeout=0.2)
            print(f"Sent: {full_cmd}")
            last_cmd = full_cmd
        except requests.exceptions.RequestException:
            print("⚠️ Failed to send command")

def detect_direction(hand_landmarks):
    fingers = []
    fingers.append(hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x)
    fingers.append(hand_landmarks.landmark[8].y < hand_landmarks.landmark[6].y)
    fingers.append(hand_landmarks.landmark[12].y < hand_landmarks.landmark[10].y)
    fingers.append(hand_landmarks.landmark[16].y < hand_landmarks.landmark[14].y)
    fingers.append(hand_landmarks.landmark[20].y < hand_landmarks.landmark[18].y)

    if fingers == [False, True, False, False, False]:
        return "F"
    elif fingers == [False, True, True, False, False]:
        return "B"
    elif fingers == [False, False, False, False, True]:
        return "L"
    elif fingers == [True, False, False, False, False]:
        return "R"
    else:
        return "S"

def distance(p1, p2, frame_shape):
    h, w = frame_shape[:2]
    x1, y1 = int(p1.x * w), int(p1.y * h)
    x2, y2 = int(p2.x * w), int(p2.y * h)
    return math.hypot(x2 - x1, y2 - y1)

# Open webcam and ESP32 video stream
cam_webcam = cv2.VideoCapture(0)
cam_esp32 = cv2.VideoCapture(ESP32_STREAM_URL)

while True:
    ret1, frame1 = cam_webcam.read()
    ret2, frame2 = cam_esp32.read()

    if ret1:
        frame1 = cv2.flip(frame1, 1)
        img_rgb = cv2.cvtColor(frame1, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)

        dir_cmd = "S"
        speed = None

        if results.multi_hand_landmarks:
            for i, handLms in enumerate(results.multi_hand_landmarks):
                handedness = results.multi_handedness[i].classification[0].label
                mp_draw.draw_landmarks(frame1, handLms, mp_hands.HAND_CONNECTIONS)

                # Right hand = Direction
                if handedness == "Right":
                    dir_cmd = detect_direction(handLms)
                    cv2.putText(frame1, f"Direction: {dir_cmd}", (10, 60),
                                cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 4)

                # Left hand = Speed (thumb-index pinch)
                if handedness == "Left":
                    d = distance(handLms.landmark[4], handLms.landmark[8], frame1.shape)
                    speed = int(np.clip(np.interp(d, [20, 200], [0, 9]), 0, 9))
                    cv2.putText(frame1, f"Speed: {speed}", (10, 140),
                                cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 4)

        send_command(dir_cmd, speed)

    else:
        frame1 = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(frame1, "❌ No Webcam", (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    if not ret2 or frame2 is None:
        frame2 = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(frame2, "❌ ESP32 Feed Not Found", (100, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    frame1 = cv2.resize(frame1, (640, 480))
    frame2 = cv2.resize(frame2, (640, 480))

    combined = np.hstack((frame1, frame2))
    # cv2.imshow("Gesture Control", frame1)
    cv2.imshow("🖐️ Gesture Control | 🤖 ESP32 Feed", combined)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cam_webcam.release()
cam_esp32.release()
cv2.destroyAllWindows()
