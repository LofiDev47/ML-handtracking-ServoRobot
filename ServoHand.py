import cv2
import mediapipe as mp
import time
import serial
import math
import os
from serial.tools import list_ports

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# -----------------------------
# SERIAL (MEGAPI)
# -----------------------------

def find_serial_port():
    ports = list(list_ports.comports())
    if not ports:
        raise RuntimeError("No serial ports detected. Connect your MegaPi or USB serial device.")

    keywords = (
        "mega",
        "megapi",
        "arduino",
        "usb serial",
        "cp210",
        "ftdi",
        "ch340",
        "usb-to-serial",
        "usb serial device",
    )

    for p in ports:
        info = " ".join(filter(None, [p.device, p.name, p.description, p.manufacturer, p.product])).lower()
        if any(keyword in info for keyword in keywords):
            print(f"Using serial port: {p.device} -> {p.description or p.product or p.name}")
            return p.device

    if len(ports) == 1:
        p = ports[0]
        print(f"Only one serial port found, using: {p.device} -> {p.description or p.product or p.name}")
        return p.device

    print("Multiple serial ports detected. Using the first available port:")
    for p in ports:
        print(f"  {p.device}: {p.description or p.product or p.name}")
    return ports[0].device

ser = serial.Serial(find_serial_port(), 115200)
time.sleep(2)

# -----------------------------
# MEDIA PIPE TASKS SETUP
# -----------------------------
BaseOptions = mp.tasks.BaseOptions
HandLandmarker = vision.HandLandmarker
HandLandmarkerOptions = vision.HandLandmarkerOptions
RunningMode = vision.RunningMode

script_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(script_dir, "hand_landmarker.task")

options = HandLandmarkerOptions(
    base_options=BaseOptions(
        model_asset_path=model_path
    ),
    running_mode=RunningMode.VIDEO,
    num_hands=1
)

landmarker = HandLandmarker.create_from_options(options)

# -----------------------------
# CAMERA
# -----------------------------
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

prev = [0, 0, 0, 0, 0]
alpha = 0.5

# -----------------------------
# HELPERS
# -----------------------------
def clamp(x):
    return max(0.0, min(1.0, x))

def dist(a, b):
    return math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2)

def finger_curl(hand, tip, pip):
    return clamp((hand[tip].y - hand[pip].y) * 5 + 0.5)

# -----------------------------
# LOOP
# -----------------------------
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    # ✅ FIXED: proper VIDEO timestamp (NO MORE FREEZE)
    timestamp = int(time.time() * 1000)

    result = landmarker.detect_for_video(mp_image, timestamp)

    # -----------------------------
    # LANDMARK DRAWING
    # -----------------------------
    if result.hand_landmarks:
        hand = result.hand_landmarks[0]

        for lm in hand:
            h, w, _ = frame.shape
            x, y = int(lm.x * w), int(lm.y * h)
            cv2.circle(frame, (x, y), 3, (0, 255, 0), -1)

        # -----------------------------
        # ROBUST FINGER MATH (FIXED)
        # -----------------------------

        wrist = hand[0]

        # THUMB (same as other fingers)
        thumb = finger_curl(hand, 4, 3)

        # INDEX (hinge curl model, same style as other fingers)
        index = finger_curl(hand, 8, 6)

        # OTHER FINGERS (stable hinge model)
        middle = finger_curl(hand, 12, 10)
        ring   = finger_curl(hand, 16, 14)
        pinky  = finger_curl(hand, 20, 18)

        vals = [thumb, index, middle, ring, pinky]
        print(f"raw: thumb={thumb:.2f} index={index:.2f} middle={middle:.2f} ring={ring:.2f} pinky={pinky:.2f}")

        # -----------------------------
        # SMOOTHING (IMPORTANT)
        # -----------------------------
        for i in range(5):
            prev[i] = prev[i] * (1 - alpha) + vals[i] * alpha

        angles = [int(v * 180) for v in prev]
        angles = [max(0, min(180, a)) for a in angles]

        # -----------------------------
        # SEND TO MEGAPI
        # -----------------------------
        ser.write(f"{angles[0]},{angles[1]},{angles[2]},{angles[3]},{angles[4]}\n".encode())

        print("ANGLES:", angles)

    # -----------------------------
    # DISPLAY
    # -----------------------------
    cv2.imshow("Robot Hand FINAL", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()