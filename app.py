import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import threading


class GreenScreenApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Green Screen Replacer")
        self.root.geometry("800x600")

        # Video preview area
        self.video_label = tk.Label(root)
        self.video_label.pack()

        # Button panel
        self.btn_frame = tk.Frame(root)
        self.btn_frame.pack(pady=10)

        self.load_bg_btn = tk.Button(
            self.btn_frame, text="Load Background", command=self.load_background
        )
        self.load_bg_btn.grid(row=0, column=0, padx=10)

        self.start_btn = tk.Button(
            self.btn_frame, text="Start Camera", command=self.start_camera
        )
        self.start_btn.grid(row=0, column=1, padx=10)

        self.stop_btn = tk.Button(
            self.btn_frame, text="Stop Camera", command=self.stop_camera
        )
        self.stop_btn.grid(row=0, column=2, padx=10)

        # Initial states
        self.running = False
        self.bg_img = None
        self.capture = None
        self.thread = None

    def load_background(self):
        """Open file dialog and load selected background image"""
        path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.jpg *.png *.jpeg *.bmp")]
        )
        if path:
            self.bg_img = cv2.imread(path)
            if self.bg_img is not None:
                print("✅ Background image loaded.")
            else:
                print("❌ Failed to load background image.")

    def start_camera(self):
        """Start webcam capture"""
        if self.running:
            return  # Prevent multiple threads

        self.running = True
        self.capture = cv2.VideoCapture(0)

        if not self.capture.isOpened():
            print("❌ Could not access the camera.")
            self.running = False
            return

        self.thread = threading.Thread(target=self.process_frames)
        self.thread.start()

    def stop_camera(self):
        """Stop webcam and release resources"""
        self.running = False
        if self.capture:
            self.capture.release()
            self.capture = None
        self.video_label.config(image="")

    def process_frames(self):
        """Main loop to process webcam frames"""
        while self.running:
            ret, frame = self.capture.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)  # Mirror image

            # Process green screen removal
            if self.bg_img is not None:
                bg_resized = cv2.resize(self.bg_img, (frame.shape[1], frame.shape[0]))
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

                lower_green = np.array([35, 40, 40])
                upper_green = np.array([85, 255, 255])
                mask = cv2.inRange(hsv, lower_green, upper_green)
                mask_inv = cv2.bitwise_not(mask)

                fg = cv2.bitwise_and(frame, frame, mask=mask_inv)
                bg = cv2.bitwise_and(bg_resized, bg_resized, mask=mask)
                combined = cv2.add(fg, bg)
            else:
                combined = frame

            # Convert BGR to RGB and update the Tkinter label
            rgb_frame = cv2.cvtColor(combined, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb_frame)
            imgtk = ImageTk.PhotoImage(image=img)

            # Update the label in the main UI thread
            self.video_label.imgtk = imgtk
            self.video_label.config(image=imgtk)

        # When stopped, release camera
        if self.capture:
            self.capture.release()


if __name__ == "__main__":
    root = tk.Tk()
    app = GreenScreenApp(root)
    root.mainloop()
