import cv2
import mediapipe as mp
import time
import serial
import math
import os
from serial.tools import list_ports

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


# SERIAL (MEGAPI)


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


# MEDIA PIPE TASKS SETUP

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


# CAMERA

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

prev = [0, 0, 0, 0, 0, 0]
alpha = 0.25
gain = 1.5          # finger sensitivity: >1 = more servo movement; tune until full open/close reaches 0-180
wrist_gain = 2.0    # wrist sensitivity: higher = more servo movement for palm spin (try 1.0 - 3.0)
wrist_range = 0.35  # radians (~20 deg) of palm rotation to map to full 0..1 range; decrease for more sensitivity
debug = True        # print raw values for tuning


# HELPERS

def clamp(x):
    return max(0.0, min(1.0, x))

def dist(a, b):
    return math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2)

def finger_curl(hand, tip, pip):
    # Steeper scaling so small finger curls use more of the servo range.
    return clamp((hand[tip].y - hand[pip].y) * 7 + 0.5)

def thumb_curl(hand):
    return clamp((dist(hand[4], hand[5]) - 0.05) * 6.0)

def wrist_angle(hand):
    # Palm roll / wrist spin: angle of the line across the palm from index MCP (5) to pinky MCP (17).
    # When the wrist spins left/right, one side of the palm rises and the other falls,
    # so this line tilts and gives a strong signal across the full rotation range.
    dx = hand[17].x - hand[5].x
    dy = hand[17].y - hand[5].y
    roll = math.atan2(dy, dx)
    # Map +/- wrist_range to 0..1, with 0.5 = palm flat facing camera.
    return clamp((roll / wrist_range) + 0.5)

# LOOP

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    # proper VIDEO timestamp
    timestamp = int(time.time() * 1000)

    result = landmarker.detect_for_video(mp_image, timestamp)


    # LANDMARK DRAWING

    if result.hand_landmarks:
        hand = result.hand_landmarks[0]

        for lm in hand:
            h, w, _ = frame.shape
            x, y = int(lm.x * w), int(lm.y * h)
            cv2.circle(frame, (x, y), 3, (0, 255, 0), -1)

        # Draw palm line to visualize wrist spin measurement.
        h, w, _ = frame.shape
        ix, iy = int(hand[5].x * w), int(hand[5].y * h)
        px, py = int(hand[17].x * w), int(hand[17].y * h)
        cv2.line(frame, (ix, iy), (px, py), (255, 0, 0), 2)


        # FINGER MATH

        thumb = thumb_curl(hand)
        index = finger_curl(hand, 8, 6)
        middle = finger_curl(hand, 12, 10)
        ring   = finger_curl(hand, 16, 14)
        pinky  = finger_curl(hand, 20, 18)
        wrist_val = wrist_angle(hand)

        vals = [thumb, index, middle, ring, pinky, wrist_val]


        # SMOOTHING (IMPORTANT)

        for i in range(6):
            prev[i] = prev[i] * (1 - alpha) + vals[i] * alpha

        angles = [int(clamp(v * gain) * 180) for v in prev]
        angles = [max(0, min(180, a)) for a in angles]
        # wrist uses its own gain (wrist_angle already returns 0..1)
        angles[5] = int(clamp(prev[5] * wrist_gain) * 180)
        angles[5] = max(0, min(180, angles[5]))

        # Reverse direction for thumb and the three inner fingers
        angles[0] = 180 - angles[0]  # thumb
        angles[2] = 180 - angles[2]  # middle
        angles[3] = 180 - angles[3]  # ring
        angles[4] = 180 - angles[4]  # pinky
        ser.write(f"{angles[0]},{angles[1]},{angles[2]},{angles[3]},{angles[4]},{angles[5]}\n".encode())

        if debug:
            print(f"RAW: t={thumb:.2f} i={index:.2f} m={middle:.2f} r={ring:.2f} p={pinky:.2f} w={wrist_val:.2f} -> ANGLES: {angles}")
        else:
            print("ANGLES:", angles)


    # DISPLAY

    cv2.imshow("Robot Hand FINAL", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
