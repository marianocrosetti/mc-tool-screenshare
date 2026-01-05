#!/usr/bin/env python3
"""
Screen Capture - Save screenshots at intervals without GUI

Usage:
    python screen_capture.py                      # Screen 1, every 3 seconds
    python screen_capture.py 1                    # Screen 1, every 3 seconds
    python screen_capture.py 1 5                  # Screen 1, every 5 seconds
    python screen_capture.py 1 3 10               # Screen 1, every 3 seconds, max 10 screenshots

Press Ctrl+C to stop.
"""

import sys
import os
import time
from datetime import datetime
import mss
import mss.tools


def list_screens():
    """List all available screens."""
    with mss.mss() as sct:
        print("\n📺 Available screens:")
        for i, monitor in enumerate(sct.monitors):
            if i == 0:
                print(f"  [0] All screens: {monitor['width']}×{monitor['height']}")
            else:
                print(f"  [{i}] Display {i}: {monitor['width']}×{monitor['height']} at ({monitor['left']},{monitor['top']})")
        return sct.monitors


def capture_screenshots(screen_num=1, interval=3, max_shots=None, output_dir="."):
    """
    Capture screenshots at regular intervals.
    
    Args:
        screen_num: Which screen to capture (0=all, 1=primary, etc.)
        interval: Seconds between captures
        max_shots: Maximum number of screenshots (None = unlimited)
        output_dir: Directory to save screenshots
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    with mss.mss() as sct:
        # Validate screen number
        if screen_num < 0 or screen_num >= len(sct.monitors):
            print(f"❌ Screen {screen_num} not found.")
            list_screens()
            return
        
        monitor = sct.monitors[screen_num]
        
        print("\n" + "=" * 50)
        print("       📸 SCREEN CAPTURE STARTED")
        print("=" * 50)
        print(f"\n  Screen: {screen_num} ({monitor['width']}×{monitor['height']})")
        print(f"  Interval: {interval} seconds")
        print(f"  Max shots: {max_shots if max_shots else 'unlimited'}")
        print(f"  Output: {os.path.abspath(output_dir)}")
        print("\n  Press Ctrl+C to stop.\n")
        print("-" * 50)
        
        count = 0
        try:
            while True:
                # Check if we've reached max shots
                if max_shots and count >= max_shots:
                    print(f"\n✅ Reached {max_shots} screenshots. Done!")
                    break
                
                # Capture screenshot
                screenshot = sct.grab(monitor)
                
                # Generate filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
                filepath = os.path.join(output_dir, filename)
                
                # Save the screenshot
                mss.tools.to_png(screenshot.rgb, screenshot.size, output=filepath)
                
                count += 1
                print(f"  [{count}] Saved: {filename}")
                
                # Wait for next capture
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print(f"\n\n🛑 Stopped. Captured {count} screenshots.")


def main():
    args = sys.argv[1:]
    
    # Default values
    screen_num = 1
    interval = 3
    max_shots = None
    
    if len(args) >= 1:
        if args[0] in ['-h', '--help', 'help']:
            print(__doc__)
            list_screens()
            return
        if args[0] == '-l' or args[0] == '--list':
            list_screens()
            return
        try:
            screen_num = int(args[0])
        except ValueError:
            print(f"❌ Invalid screen number: {args[0]}")
            return
    
    if len(args) >= 2:
        try:
            interval = float(args[1])
        except ValueError:
            print(f"❌ Invalid interval: {args[1]}")
            return
    
    if len(args) >= 3:
        try:
            max_shots = int(args[2])
        except ValueError:
            print(f"❌ Invalid max shots: {args[2]}")
            return
    
    capture_screenshots(screen_num, interval, max_shots)


if __name__ == "__main__":
    main()

