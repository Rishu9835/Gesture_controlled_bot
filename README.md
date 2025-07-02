# 🤖 Gesture Controlled Bot

## A real-time gesture-controlled robot that uses hand tracking powered by MediaPipe and OpenCV to control an ESP32-CAM-based robotic car. The bot streams live video and responds to directional and speed gestures from your hands.

## 🚀 Features
	•	Real-time gesture recognition using MediaPipe
	•	ESP32-CAM live video streaming
	•	Two-hand control system:
	•	Right hand: Direction (Forward, Left, Right, Back, Stop)
	•	Left hand: Speed control using thumb–index finger distance
	•	Wireless communication via HTTP requests to ESP32
	•	Easy to set up and modify
## 🧠 How It Works
	•	Right Hand (Direction):
	•	✊ Fist = Stop
	•	☝️ One Finger = Forward
	•	✌️ Two Fingers = Backward
	•	👍 thumb = Right
	•	🤙 little finger = Backward
	•	Left Hand (Speed):
	•	Distance between thumb and index finger controls speed (scaled 0–9)

### The PC uses OpenCV + MediaPipe to detect hand landmarks and send direction/speed commands via Wi-Fi to the ESP32-CAM. The ESP32 controls motor speed using PWM.

## 🛠️ Tech Stack
	•	ESP32-CAM (Arduino Framework)
	•	Python (OpenCV + MediaPipe)
	•	HTTP communication between PC and ESP32
	•	Motors controlled via L298N or motor driver module

# 🔧 Setup Instructions

## 1. Hardware Requirements
	•	ESP32-CAM module
	•	Motor driver (e.g., L298N)
	•	2 DC Motors
	•	Power supply (Li-ion or USB)
	•	Laptop/PC with Wi-Fi

## 2. ESP32 Setup
	•	Flash the gesture_bot.ino using Arduino IDE
	•	Set your Wi-Fi SSID and password in the code
	•	ESP32 starts a video stream and listens to commands via /move?cmd= endpoint
 ### NOTE-DOWNLOAD NECESSARY LIBRARIES BEFORE STARTUP IN requirements.txt
