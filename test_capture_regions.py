#!/usr/bin/env python3
import os
import time
import subprocess
from datetime import datetime
from PIL import Image
import config
SCREENSHOT_FILENAME = 'captures/screenshot.png'


def capture_and_save(region, save_dir, prefix):
    # Take full-screen screenshot via adb
    os.makedirs(save_dir, exist_ok=True)
    with open(SCREENSHOT_FILENAME, 'wb') as f:
        subprocess.run([config.ADB_PATH, 'exec-out', 'screencap', '-p'], stdout=f)
    # Load the screenshot
    img = Image.open(SCREENSHOT_FILENAME)
    x, y, w, h = region
    # Crop the region of interest
    cropped = img.crop((x, y, x + w, y + h))
    # Generate a timestamped filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    filename = f"{prefix}_{timestamp}.png"
    filepath = os.path.join(save_dir, filename)
    # Save cropped image
    cropped.save(filepath)
    print(f"Saved {filepath}")


def main():
    # Directories to store captures
    capture_dir = os.path.join('captures')
    interval = 0.5  # seconds between captures

    print("Starting capture loop. Press Ctrl+C to stop.")
    try:
        while True:
            capture_and_save(config.MODE_REGION, capture_dir, 'mode')
            capture_and_save(config.MAP_REGION, capture_dir, 'map')
            time.sleep(interval)
    except KeyboardInterrupt:
        print("Capture loop stopped by user.")


if __name__ == '__main__':
    main() 