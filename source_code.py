import cv2
import requests
import time
import os
import sys

os.environ['DISPLAY'] = ':0'

SERVER_URL = 'https://www.circuitdigest.cloud/api/v1/object-detection/detect'
API_KEY = 'cd_tri_240926_DFNic5'
CLASSES = []
CONFIDENCE = 0.2

MODE = 'auto'
AUTO_INTERVAL = 5

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    print("Where's your camera? Please check the connection.")
    sys.exit()
print("Camera initialized.")
print(f"Running in [{MODE}] mode")

if MODE == "keyboard":
    print("Press SPACE to capture | Press ESC to quit")
elif MODE == "auto":
    print(f"Auto capturing every {AUTO_INTERVAL} seconds | Press ESC to quit")
elif MODE == "ssh":
    print("Auto capturing every 5 seconds | Press Ctrl+C to quit")

def send_image_to_api(frame):
    for _ in range(3):
        cap.read()
    ret, frame = cap.read()
    if not ret:
        print("Capture failed")
        return

    _, img_encoded = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    img_bytes = img_encoded.tobytes()

    headers = { "X-API-Key": API_KEY }
    files   = { "imageFile": ("photo.jpg", img_bytes, "image/jpeg") }
    data    = { "classes": CLASSES, "confidence": CONFIDENCE }

    try:
        print("\nSending to Object Detection API...")
        response = requests.post(SERVER_URL, headers=headers,
                                 files=files, data=data, timeout=15)

        if response.status_code == 200:
            result = response.json()

            # ? Fixed encoding issue
            safe_response = response.text.encode('utf-8', errors='replace').decode('utf-8')
            print("Response:", safe_response)

            count = result.get("detection_count", 0)
            print(f"Objects detected: {count}")

            for det in result.get("detections", []):
                label = det.get("class_name") or det.get("class", "unknown")
                conf  = det.get("confidence", 0)
                # ? Fixed encoding for label too
                safe_label = str(label).encode('utf-8', errors='replace').decode('utf-8')
                print(f"  - {safe_label} ({conf:.2f}%)")
        else:
            print(f"HTTP error: {response.status_code}")

    except requests.exceptions.Timeout:
        print("Request timed out!")
    except Exception as e:
        print(f"Error: {str(e).encode('utf-8', errors='replace').decode('utf-8')}")

if MODE == "ssh":
    try:
        while True:
            ret, frame = cap.read()
            if ret:
                print("\nAuto capturing...")
                send_image_to_api(frame)
            time.sleep(AUTO_INTERVAL)
    except KeyboardInterrupt:
        print("Stopped by user.")
    finally:
        cap.release()

else:
    last_capture_time = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        cv2.imshow("Camera - SPACE: capture | ESC: quit", frame)

        key = cv2.waitKey(1) & 0xFF

        if MODE == "keyboard":
            if key == 32:
                print("\nCapturing image...")
                send_image_to_api(frame)

        elif MODE == "auto":
            current_time = time.time()
            if current_time - last_capture_time >= AUTO_INTERVAL:
                last_capture_time = current_time
                print("\nAuto capturing...")
                send_image_to_api(frame)

        if key == 27:
            print("Quitting...")
            break

    cap.release()
    cv2.destroyAllWindows()

    