#!/usr/bin/env python3
"""
Screen Capture - Save screenshots at intervals without GUI

Usage:
    python screen_capture.py -l                   # List available screens
    python screen_capture.py 2 --single           # Take ONE screenshot of screen 2
    python screen_capture.py 2 -1                 # Same as above (shorthand)
    python screen_capture.py 2 --fast             # Fast mode: JPEG instead of PNG
    python screen_capture.py 2 -1 --fast          # Single + fast combined
    python screen_capture.py 2 -f -o /tmp         # Fast mode, save to /tmp
    python screen_capture.py                      # Screen 1, every 3 seconds
    python screen_capture.py 1                    # Screen 1, every 3 seconds
    python screen_capture.py 1 5                  # Screen 1, every 5 seconds
    python screen_capture.py 1 3 10               # Screen 1, every 3 seconds, max 10 screenshots

Options:
    -l, --list          List available screens
    -1, -s, --single    Take a single screenshot
    -f, --fast          Use JPEG format (faster)
    -o, --output DIR    Save to specified directory

Press Ctrl+C to stop interval captures.
"""

import sys
import os
import time
from datetime import datetime
import mss
from PIL import Image


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


def capture_single_native(screen_num=1, output_dir=".", fast=False, debug=True):
    """
    Capture using macOS native screencapture (FAST!).
    
    Args:
        screen_num: Which screen to capture (1=primary, 2=secondary, etc.)
        output_dir: Directory to save screenshot
        fast: If True, use JPEG instead of PNG
        debug: If True, show timing
    
    Returns:
        Path to saved file, or None on error
    """
    import subprocess
    import time as t
    
    total_start = t.perf_counter()
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = "jpg" if fast else "png"
    filename = f"screenshot_{timestamp}.{ext}"
    filepath = os.path.join(output_dir, filename)
    
    # macOS screencapture: -D selects display (1-indexed)
    # -t specifies format, -x suppresses sound
    cmd = ["screencapture", "-D", str(screen_num), "-t", ext, "-x", filepath]
    
    if debug:
        print(f"⏱️  Running: {' '.join(cmd)}")
    
    stage_start = t.perf_counter()
    result = subprocess.run(cmd, capture_output=True, text=True)
    capture_time = (t.perf_counter() - stage_start) * 1000
    
    if result.returncode != 0:
        print(f"❌ screencapture failed: {result.stderr}")
        return None
    
    if not os.path.exists(filepath):
        print(f"❌ File not created")
        return None
    
    total_time = (t.perf_counter() - total_start) * 1000
    
    if debug:
        print(f"⏱️  Capture time: {capture_time:.1f}ms")
    
    print(f"\n📸 Saved: {filepath}")
    print(f"   Total time: {total_time:.1f}ms")
    
    return filepath


def capture_single(screen_num=1, output_dir=".", fast=False, debug=True):
    """
    Capture a single screenshot immediately.
    Uses native macOS screencapture for speed.
    
    Args:
        screen_num: Which screen to capture (0=all, 1=primary, etc.)
        output_dir: Directory to save screenshot
        fast: If True, use JPEG (faster) instead of PNG
        debug: If True, show timing for each stage
    
    Returns:
        Path to saved file, or None on error
    """
    import platform
    
    # Use native macOS screencapture if available (MUCH faster)
    if platform.system() == "Darwin" and screen_num > 0:
        return capture_single_native(screen_num, output_dir, fast, debug)
    
    # Fallback to mss for other platforms or screen 0 (all screens)
    import time as t
    
    total_start = t.perf_counter()
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Stage 1: Initialize mss
    stage_start = t.perf_counter()
    sct = mss.mss()
    if debug:
        print(f"⏱️  [1] mss init: {(t.perf_counter() - stage_start)*1000:.1f}ms")
    
    if screen_num < 0 or screen_num >= len(sct.monitors):
        print(f"❌ Screen {screen_num} not found.")
        list_screens()
        sct.close()
        return None
    
    monitor = sct.monitors[screen_num]
    
    # Stage 2: Grab screen
    stage_start = t.perf_counter()
    screenshot = sct.grab(monitor)
    if debug:
        print(f"⏱️  [2] Screen grab: {(t.perf_counter() - stage_start)*1000:.1f}ms")
    
    # Stage 3: Convert to PIL Image
    stage_start = t.perf_counter()
    img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
    if debug:
        print(f"⏱️  [3] PIL convert: {(t.perf_counter() - stage_start)*1000:.1f}ms")
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Stage 4: Save to disk
    stage_start = t.perf_counter()
    if fast:
        filename = f"screenshot_{timestamp}.jpg"
        filepath = os.path.join(output_dir, filename)
        img.save(filepath, format="JPEG", quality=85)
    else:
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(output_dir, filename)
        img.save(filepath, format="PNG", compress_level=1)
    if debug:
        print(f"⏱️  [4] Save to disk: {(t.perf_counter() - stage_start)*1000:.1f}ms")
    
    sct.close()
    
    total_time = (t.perf_counter() - total_start) * 1000
    print(f"\n📸 Saved: {filepath}")
    print(f"   Screen {screen_num}: {monitor['width']}×{monitor['height']}")
    print(f"   Total time: {total_time:.1f}ms")
    
    return filepath


def capture_screenshots(screen_num=1, interval=3, max_shots=None, output_dir="."):
    """
    Capture screenshots at regular intervals.
    
    Args:
        screen_num: Which screen to capture (0=all, 1=primary, etc.)
        interval: Seconds between captures
        max_shots: Maximum number of screenshots (None = unlimited)
        output_dir: Directory to save screenshots
    """
    os.makedirs(output_dir, exist_ok=True)
    
    with mss.mss() as sct:
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
                
                # Convert to PIL Image
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                
                # Generate filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
                filepath = os.path.join(output_dir, filename)
                
                # Save the screenshot
                img.save(filepath, format="PNG")
                
                count += 1
                print(f"  [{count}] Saved: {filename}")
                
                # Only wait if we need more shots
                if max_shots is None or count < max_shots:
                    time.sleep(interval)
                
        except KeyboardInterrupt:
            print(f"\n\n🛑 Stopped. Captured {count} screenshots.")


def parse_args(args):
    """Parse command line arguments."""
    result = {
        'screen_num': 1,
        'single': False,
        'fast': False,
        'output_dir': '.',
        'interval': 3,
        'max_shots': None,
        'list': False,
        'help': False,
    }
    
    i = 0
    while i < len(args):
        arg = args[i]
        
        if arg in ['-h', '--help', 'help']:
            result['help'] = True
            return result
        elif arg in ['-l', '--list']:
            result['list'] = True
            return result
        elif arg in ['-1', '-s', '--single']:
            result['single'] = True
        elif arg in ['-f', '--fast']:
            result['fast'] = True
        elif arg in ['-o', '--output']:
            if i + 1 < len(args):
                i += 1
                result['output_dir'] = args[i]
            else:
                print("❌ --output requires a directory path")
                return None
        else:
            # Try to parse as number
            try:
                num = int(arg)
                # First number is screen_num, second is interval, third is max_shots
                if result['screen_num'] == 1 and not any(a.isdigit() for a in args[:i]):
                    result['screen_num'] = num
                elif result['interval'] == 3:
                    result['interval'] = num
                else:
                    result['max_shots'] = num
            except ValueError:
                try:
                    result['interval'] = float(arg)
                except ValueError:
                    print(f"❌ Unknown argument: {arg}")
                    return None
        i += 1
    
    return result


def main():
    args = parse_args(sys.argv[1:])
    
    if args is None:
        return
    
    if args['help']:
        print(__doc__)
        list_screens()
        return
    
    if args['list']:
        list_screens()
        return
    
    # Single screenshot mode
    if args['single'] or args['fast']:
        capture_single(
            screen_num=args['screen_num'],
            output_dir=args['output_dir'],
            fast=args['fast']
        )
        return
    
    # Continuous capture mode
    capture_screenshots(
        screen_num=args['screen_num'],
        interval=args['interval'],
        max_shots=args['max_shots'],
        output_dir=args['output_dir']
    )


if __name__ == "__main__":
    main()
