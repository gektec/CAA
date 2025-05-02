#!/usr/bin/env python3
"""
Simple script to click specified coordinates via ADB.
"""

import subprocess
import time
import argparse
import config
import os
import io
from PIL import Image


def tap(x, y):
    """Send an adb tap command to the device at (x, y)."""
    cmd = [config.ADB_PATH, 'shell', 'input', 'tap', str(x), str(y)]
    subprocess.run(cmd, check=True)


def capture_region(x, y, width=440, height=200):
    """Capture a region of size width x height centered at (x, y) and save it to the capture folder."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    capture_dir = os.path.join(script_dir, 'captures')
    os.makedirs(capture_dir, exist_ok=True)
    proc = subprocess.run([config.ADB_PATH, 'exec-out', 'screencap', '-p'], stdout=subprocess.PIPE, check=True)
    img = Image.open(io.BytesIO(proc.stdout))
    left = x - width // 2
    top = y - height // 2
    right = left + width
    bottom = top + height
    region = img.crop((left, top, right, bottom))
    filename = f"{x}_{y}.png"
    path = os.path.join(capture_dir, filename)
    region.save(path)
    print(f"Saved capture region to {path}")


def main():
    parser = argparse.ArgumentParser(description='Tap on specified coordinates via ADB.')
    parser.add_argument('x', type=int, help='X coordinate')
    parser.add_argument('y', type=int, help='Y coordinate')
    parser.add_argument('--wait', type=float, default=config.WAIT_TIME, help='Wait time after tap (seconds)')
    args = parser.parse_args()

    print(f"Clicking at ({args.x}, {args.y}) with wait_time={args.wait}s...")
    # tap(args.x, args.y)
    time.sleep(args.wait)
    capture_region(args.x, args.y)
    print("Done.")


if __name__ == "__main__":
    main() 