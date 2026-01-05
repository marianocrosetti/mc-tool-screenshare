#!/usr/bin/env python3
"""
Screen Share CLI - Share your screen from the command line
Usage:
    python screen_share_cli.py              # Interactive mode - lists screens and lets you choose
    python screen_share_cli.py 1            # Share screen 1
    python screen_share_cli.py 1920 1080    # Share custom region (width height)
    python screen_share_cli.py 1920 1080 0 0  # Share custom region (width height left top)

Press 'q' to stop sharing.
"""

import sys
import mss
import cv2
import numpy as np


def list_screens():
    """List all available screens."""
    with mss.mss() as sct:
        print("\n" + "=" * 50)
        print("       📺 AVAILABLE SCREENS")
        print("=" * 50 + "\n")
        
        for i, monitor in enumerate(sct.monitors):
            if i == 0:
                print(f"  [0] All screens combined")
                print(f"      Size: {monitor['width']} × {monitor['height']}\n")
            else:
                print(f"  [{i}] Display {i}")
                print(f"      Size: {monitor['width']} × {monitor['height']}")
                print(f"      Position: ({monitor['left']}, {monitor['top']})\n")
        
        return sct.monitors


def select_screen_interactive():
    """Interactive screen selection in terminal."""
    monitors = list_screens()
    
    while True:
        try:
            choice = input("👉 Enter screen number to share (or 'q' to quit): ").strip()
            
            if choice.lower() == 'q':
                return None
            
            idx = int(choice)
            if 0 <= idx < len(monitors):
                return monitors[idx]
            
            print(f"❌ Invalid choice. Enter a number between 0 and {len(monitors) - 1}")
        except ValueError:
            print("❌ Please enter a valid number")


def create_custom_monitor(width, height, left=0, top=0):
    """Create a custom monitor region."""
    return {
        "left": left,
        "top": top,
        "width": width,
        "height": height
    }


def start_screen_share(monitor):
    """Start capturing and displaying the screen."""
    print(f"\n✅ Screen sharing started!")
    print(f"   Region: {monitor['width']} × {monitor['height']}")
    print(f"   Position: ({monitor['left']}, {monitor['top']})")
    print("\n💡 Press 'q' in the preview window to stop sharing.\n")
    
    with mss.mss() as sct:
        while True:
            # Capture the screen
            screenshot = sct.grab(monitor)
            frame = np.array(screenshot)
            
            # Convert BGRA to BGR for OpenCV
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            
            # Resize for preview if too large
            height, width = frame.shape[:2]
            max_width = 1280
            if width > max_width:
                scale = max_width / width
                frame = cv2.resize(frame, (int(width * scale), int(height * scale)))
            
            # Add LIVE indicator
            cv2.circle(frame, (30, 30), 10, (0, 0, 255), -1)
            cv2.putText(frame, "LIVE", (50, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            
            # Show frame
            cv2.imshow("Screen Share - Press 'q' to stop", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    cv2.destroyAllWindows()
    print("🛑 Screen sharing stopped.")


def print_usage():
    """Print usage information."""
    print("""
📖 USAGE:
    python screen_share_cli.py                    # Interactive mode
    python screen_share_cli.py <screen_number>    # Share specific screen
    python screen_share_cli.py <width> <height>   # Custom region from (0,0)
    python screen_share_cli.py <width> <height> <left> <top>  # Custom region

📝 EXAMPLES:
    python screen_share_cli.py 1                  # Share display 1
    python screen_share_cli.py 1920 1080          # Share 1920x1080 from top-left
    python screen_share_cli.py 800 600 100 100    # Share 800x600 starting at (100,100)
""")


def main():
    args = sys.argv[1:]
    
    if len(args) == 0:
        # Interactive mode
        monitor = select_screen_interactive()
        if monitor:
            start_screen_share(monitor)
        else:
            print("❌ Cancelled.")
    
    elif len(args) == 1:
        # Single argument: screen number or help
        if args[0] in ['-h', '--help', 'help']:
            print_usage()
            return
        
        try:
            screen_num = int(args[0])
            with mss.mss() as sct:
                if 0 <= screen_num < len(sct.monitors):
                    start_screen_share(sct.monitors[screen_num])
                else:
                    print(f"❌ Screen {screen_num} not found.")
                    list_screens()
        except ValueError:
            print(f"❌ Invalid screen number: {args[0]}")
            print_usage()
    
    elif len(args) == 2:
        # Two arguments: width height
        try:
            width = int(args[0])
            height = int(args[1])
            monitor = create_custom_monitor(width, height)
            print(f"📐 Custom region: {width} × {height} from (0, 0)")
            start_screen_share(monitor)
        except ValueError:
            print("❌ Width and height must be numbers")
            print_usage()
    
    elif len(args) == 4:
        # Four arguments: width height left top
        try:
            width = int(args[0])
            height = int(args[1])
            left = int(args[2])
            top = int(args[3])
            monitor = create_custom_monitor(width, height, left, top)
            print(f"📐 Custom region: {width} × {height} from ({left}, {top})")
            start_screen_share(monitor)
        except ValueError:
            print("❌ All arguments must be numbers")
            print_usage()
    
    else:
        print("❌ Invalid number of arguments")
        print_usage()


if __name__ == "__main__":
    main()

