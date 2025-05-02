# adb_controller.py
import subprocess
import time
from config import ADB_PATH, WAIT_TIME, FULL_SCREENSHOT_PATH
from PIL import Image
import io



def connect_device():
    """
    Connect to Android emulator/device via ADB.
    """
    try:
        subprocess.run([ADB_PATH, 'connect', '127.0.0.1:16384'], check=True)
        print("Connected to Android emulator at 127.0.0.1:16384")
        # subprocess.run([ADB_PATH, 'connect', '127.0.0.1:16416'], check=True)
        # print("Connected to Android emulator at 127.0.0.1:16416")
    except subprocess.CalledProcessError as e:
        print(f"Error connecting via ADB: {e}")

# Automatically connect when module is imported
connect_device()

def take_screenshot():
    """
    Capture a screenshot from the connected Android emulator/device and return a PIL Image.
    """
    # Use adb exec-out to capture screen in PNG format
    try:
        result = subprocess.run(
            [ADB_PATH, 'exec-out', 'screencap', '-p'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        img_data = result.stdout
        img = Image.open(io.BytesIO(img_data))
        # Optionally save to file
        img.save(FULL_SCREENSHOT_PATH)
        return img
    except subprocess.CalledProcessError as e:
        print(f"Error taking screenshot: {e}")
        return None


def tap(x, y):
    """
    Simulate a tap on the device at (x, y).
    """
    try:
        subprocess.run([ADB_PATH, 'shell', 'input', 'tap', str(x), str(y)], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error tapping at ({x}, {y}): {e}")


def wait():
    """
    Wait for a predefined amount of time.
    """
    time.sleep(WAIT_TIME) 