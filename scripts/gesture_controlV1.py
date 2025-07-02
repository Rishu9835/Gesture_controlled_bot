import cv2
import mediapipe as mp
import requests
import numpy as np

# === CONFIG ===
ESP32_STREAM_URL = "http://192.168.250.163:81"
ESP32_CMD_URL = "http://192.168.250.163/move?cmd="

# === Setup ===
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

last_cmd = ""
current_speed = 0

def send_command(cmd):
    global last_cmd
    if cmd != last_cmd:
        try:
            requests.get(ESP32_CMD_URL + cmd, timeout=0.2)
            print(f"Sent: {cmd}")
            last_cmd = cmd
        except requests.exceptions.RequestException:
            print("⚠️ Failed to send command")

def count_raised_fingers(hand_landmarks):
    fingers = [
        hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x,
        hand_landmarks.landmark[8].y < hand_landmarks.landmark[6].y,
        hand_landmarks.landmark[12].y < hand_landmarks.landmark[10].y,
        hand_landmarks.landmark[16].y < hand_landmarks.landmark[14].y,
        hand_landmarks.landmark[20].y < hand_landmarks.landmark[18].y,
    ]
    return sum(fingers)

def detect_direction_gesture(hand_landmarks):
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

# === Camera Setup ===
cam_webcam = cv2.VideoCapture(0)
cam_esp32 = cv2.VideoCapture(ESP32_STREAM_URL)

while True:
    ret1, frame1 = cam_webcam.read()
    ret2, frame2 = cam_esp32.read()

    direction = "S"

    if ret1:
        frame1 = cv2.flip(frame1, 1)
        img_rgb = cv2.cvtColor(frame1, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)

        if results.multi_hand_landmarks and results.multi_handedness:
            for i, handLms in enumerate(results.multi_hand_landmarks):
                handedness = results.multi_handedness[i].classification[0].label
                mp_draw.draw_landmarks(frame1, handLms, mp_hands.HAND_CONNECTIONS)

                cx = int(handLms.landmark[0].x * frame1.shape[1])
                cy = int(handLms.landmark[0].y * frame1.shape[0])
                cv2.putText(frame1, f"{handedness} Hand", (cx, cy - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

                if handedness == "Right":
                    direction = detect_direction_gesture(handLms)
                elif handedness == "Left":
                    current_speed = count_raised_fingers(handLms)
                    current_speed = min(current_speed, 5)  # Limit to max 5

        # Send combined command
        send_command(direction + str(current_speed))

        # Show direction and speed
        cv2.putText(frame1, f"Dir: {direction}", (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame1, f"Speed: {current_speed}", (10, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

        # Draw speed bar
        bar_x = 10
        bar_y = 100
        bar_width = 200
        bar_height = 20
        unit_width = bar_width // 5
        for i in range(current_speed):
            cv2.rectangle(frame1, (bar_x + i * unit_width, bar_y),
                          (bar_x + (i + 1) * unit_width - 2, bar_y + bar_height), (0, 255, 0), -1)
        cv2.rectangle(frame1, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (255, 255, 255), 2)

    else:
        frame1 = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(frame1, "❌ No Webcam", (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    # ESP32 feed
    if not ret2 or frame2 is None:
        frame2 = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(frame2, "❌ ESP32 Feed Not Found", (100, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    frame1 = cv2.resize(frame1, (640, 480))
    frame2 = cv2.resize(frame2, (640, 480))

    # Show windows
    cv2.imshow("🖐️ Gesture Control", frame1)
    #cv2.imshow("🤖 ESP32-CAM Feed", frame2)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cam_webcam.release()
cam_esp32.release()
cv2.destroyAllWindows()