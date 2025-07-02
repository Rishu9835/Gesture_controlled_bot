import cv2
import mediapipe as mp
import requests
import numpy as np

# === CONFIG ===
ESP32_STREAM_URL = "http://192.168.250.163:81"
ESP32_CMD_URL = "http://192.168.250.163/move?cmd="

# === Setup ===
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

last_cmd = ""

def send_command(cmd):
    global last_cmd
    if cmd != last_cmd:
        try:
            requests.get(ESP32_CMD_URL + cmd, timeout=0.2)
            print(f"Sent: {cmd}")
            last_cmd = cmd
        except requests.exceptions.RequestException:
            print("⚠️ Failed to send command")

def detect_gesture(hand_landmarks):
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

# Open both webcam and ESP32 stream
cam_webcam = cv2.VideoCapture(0)
cam_esp32 = cv2.VideoCapture(ESP32_STREAM_URL)

while True:
    ret1, frame1 = cam_webcam.read()
    ret2, frame2 = cam_esp32.read()

    # Process gesture from webcam
    if ret1:
        img_rgb = cv2.cvtColor(frame1, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)

        if results.multi_hand_landmarks:
            for handLms in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame1, handLms, mp_hands.HAND_CONNECTIONS)
                cmd = detect_gesture(handLms)
                send_command(cmd)
                cv2.putText(frame1, f"Gesture: {cmd}", (10, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)

    else:
        frame1 = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(frame1, "❌ No Webcam", (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    # ESP32 stream
    if not ret2 or frame2 is None:
        frame2 = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(frame2, "❌ ESP32 Feed Not Found", (100, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    # Resize and stack side by side
    frame1 = cv2.resize(frame1, (640, 480))
    frame2 = cv2.resize(frame2, (640, 480))
    combined = np.hstack((frame1, frame2))

    cv2.imshow("🖐️ Gesture Control | 🤖 ESP32 Feed", combined)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cam_webcam.release()
cam_esp32.release()
cv2.destroyAllWindows()