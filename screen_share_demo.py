#!/usr/bin/env python3
"""
Screen Share Demo - Chrome-like screen selection and sharing
Press 'q' to stop sharing once started.
"""

import mss
import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk


class ScreenShareApp:
    """A Chrome-like screen sharing application."""
    
    def __init__(self):
        self.selected_monitor = None
        self.sct = mss.mss()
        self.thumbnails = []
        self.root = None
        
    def create_thumbnail(self, monitor, size=(180, 100)):
        """Create a thumbnail preview of a monitor."""
        try:
            screenshot = self.sct.grab(monitor)
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            img.thumbnail(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Error creating thumbnail: {e}")
            return None
    
    def on_select(self, monitor_index):
        """Handle screen selection."""
        self.selected_monitor = self.sct.monitors[monitor_index]
        print(f"Selected monitor {monitor_index}")
        if self.root:
            self.root.quit()
            self.root.destroy()
    
    def on_cancel(self):
        """Handle cancel button."""
        self.selected_monitor = None
        if self.root:
            self.root.quit()
            self.root.destroy()
    
    def show_dialog(self):
        """Show the screen selection dialog."""
        self.root = tk.Tk()
        self.root.title("Share your screen")
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(False, False)
        
        # Calculate window size based on number of monitors
        num_monitors = len(self.sct.monitors) - 1  # Exclude "all monitors" option
        window_height = min(150 + (num_monitors * 140), 500)
        window_width = 450
        
        # Center the window
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Header
        header = tk.Frame(self.root, bg="#1e1e2e")
        header.pack(fill="x", pady=(20, 10))
        
        title = tk.Label(
            header, 
            text="🖥️ Choose a screen to share",
            font=("Helvetica", 16, "bold"),
            fg="#cdd6f4",
            bg="#1e1e2e"
        )
        title.pack()
        
        # Main content area
        content = tk.Frame(self.root, bg="#1e1e2e")
        content.pack(fill="both", expand=True, padx=20, pady=10)
        
        monitors = self.sct.monitors
        
        # Create a card for each screen (skip index 0 which is "all monitors")
        for i in range(1, len(monitors)):
            monitor = monitors[i]
            
            # Card frame
            card = tk.Frame(content, bg="#313244", padx=10, pady=10)
            card.pack(fill="x", pady=5)
            
            # Left side: thumbnail
            thumb_frame = tk.Frame(card, bg="#1e1e2e", padx=2, pady=2)
            thumb_frame.pack(side="left")
            
            thumb = self.create_thumbnail(monitor)
            if thumb:
                self.thumbnails.append(thumb)
                thumb_label = tk.Label(thumb_frame, image=thumb, bg="#1e1e2e")
                thumb_label.pack()
            else:
                placeholder = tk.Label(
                    thumb_frame, 
                    text="📺", 
                    font=("Helvetica", 32),
                    bg="#1e1e2e",
                    fg="#cdd6f4",
                    width=8,
                    height=2
                )
                placeholder.pack()
            
            # Middle: info
            info_frame = tk.Frame(card, bg="#313244")
            info_frame.pack(side="left", fill="both", expand=True, padx=15)
            
            name_label = tk.Label(
                info_frame,
                text=f"Display {i}",
                font=("Helvetica", 12, "bold"),
                fg="#cdd6f4",
                bg="#313244",
                anchor="w"
            )
            name_label.pack(anchor="w", pady=(5, 2))
            
            size_label = tk.Label(
                info_frame,
                text=f"{monitor['width']} × {monitor['height']}",
                font=("Helvetica", 10),
                fg="#a6adc8",
                bg="#313244",
                anchor="w"
            )
            size_label.pack(anchor="w")
            
            # Right side: Share button
            # Use a closure to capture the correct index
            def make_callback(idx):
                return lambda: self.on_select(idx)
            
            share_btn = tk.Button(
                card,
                text="  Share  ",
                font=("Helvetica", 11, "bold"),
                bg="#89b4fa",
                fg="#1e1e2e",
                activebackground="#b4befe",
                activeforeground="#1e1e2e",
                relief="flat",
                cursor="hand2",
                command=make_callback(i)
            )
            share_btn.pack(side="right", padx=5, pady=10)
        
        # Footer with cancel button
        footer = tk.Frame(self.root, bg="#1e1e2e")
        footer.pack(fill="x", pady=15)
        
        cancel_btn = tk.Button(
            footer,
            text="  Cancel  ",
            font=("Helvetica", 10),
            bg="#45475a",
            fg="#cdd6f4",
            activebackground="#585b70",
            activeforeground="#cdd6f4",
            relief="flat",
            cursor="hand2",
            command=self.on_cancel
        )
        cancel_btn.pack()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_cancel)
        
        # Run the dialog
        self.root.mainloop()
        
        return self.selected_monitor


def start_screen_share(monitor):
    """Start capturing and displaying the selected screen."""
    print(f"\n✅ Screen sharing started!")
    print(f"   Resolution: {monitor['width']} × {monitor['height']}")
    print(f"   Position: ({monitor['left']}, {monitor['top']})")
    print("\n💡 Press 'q' in the preview window to stop sharing.\n")
    
    with mss.mss() as sct:
        while True:
            # Capture the screen
            screenshot = sct.grab(monitor)
            frame = np.array(screenshot)
            
            # Convert BGRA to BGR for OpenCV
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            
            # Resize for preview if the screen is large
            height, width = frame.shape[:2]
            max_width = 1280
            if width > max_width:
                scale = max_width / width
                new_width = int(width * scale)
                new_height = int(height * scale)
                frame = cv2.resize(frame, (new_width, new_height))
            
            # Add a "LIVE" indicator
            cv2.circle(frame, (30, 30), 10, (0, 0, 255), -1)
            cv2.putText(
                frame, 
                "LIVE", 
                (50, 38),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2
            )
            
            # Show the frame
            cv2.imshow("Screen Share Preview - Press 'q' to stop", frame)
            
            # Check for quit key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    cv2.destroyAllWindows()
    print("🛑 Screen sharing stopped.")


def main():
    """Main function to run the screen share demo."""
    print("=" * 50)
    print("       🖥️  SCREEN SHARE DEMO")
    print("=" * 50)
    print("\nOpening screen selection dialog...\n")
    
    # Show the selection dialog
    app = ScreenShareApp()
    selected_monitor = app.show_dialog()
    
    if selected_monitor:
        start_screen_share(selected_monitor)
    else:
        print("❌ Screen sharing cancelled by user.")
    
    print("\nDemo finished. Goodbye! 👋")


if __name__ == "__main__":
    main()
