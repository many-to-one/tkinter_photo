import customtkinter as ctk
import threading
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import cv2

from PIL import Image

from adjustments.brightness import apply_brightness
from adjustments.contrast import apply_contrast
from adjustments.saturation import adjust_saturation_rgb
from adjustments.curve import *
from adjustments.shadows_lights import adjust_shadows_lights
from adjustments.white_balance import *
from adjustments.dehaze_effect import dehaze_effect
from adjustments.fog_effect import fog_effect
from adjustments.hsl import *
from adjustments.tiles import *
from adjustments.camera_calibration import *


class InitWindow(ctk.CTkToplevel):
    def __init__(self, parent, text):
        super().__init__(parent)

        self.title("Image Editor")
        self.geometry("300x100")
        self.grab_set()  # Block interaction with main window
        self.resizable(False, False)

        # Get screen width and height from parent
        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()

        # Calculate position to center window
        window_width = 300
        window_height = 100
        x_position = (screen_width // 2) - (window_width // 2)
        y_position = (screen_height // 2) - (window_height // 2)

        # Apply centered geometry
        self.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

        # Display message
        label = ctk.CTkLabel(self, text=text, font=ctk.CTkFont(size=14), text_color="white")
        label.pack(expand=True, fill="both", padx=10, pady=10)

        # Create indeterminate progress bar
        self.progress_bar = ctk.CTkProgressBar(self, mode="indeterminate", width=200)
        self.progress_bar.pack(pady=10)
        self.progress_bar.start()

        self.progress_percent_label = ctk.CTkLabel(
        self, text="0%", text_color="white", font=("Arial", 12)
        )
        self.progress_percent_label.pack(pady=(0, 10))

        threading.Thread(target=self.run_init, args=(self.run_warmup_and_close_info,), daemon=True).start()

    def run_init(self, target):
        """Execute the function and close the info window when done."""
        target()  # Run the function
        self.destroy()


    def start_init_window(self, target, text):
        self.show_info_window(text)
        threading.Thread(target=target, daemon=True).start()

    def run_warmup_and_close_info(self):
        # self.warm_up_processing()
        self.warm_up_processing(progress_callback=self.update_progress)
        # self.info_window.after(0, self.info_window.destroy)


    def warm_up_processing(self, progress_callback=None):

        dummy = np.zeros((2000, 2000, 3), dtype=np.uint8)
        self.update_progress(0)
        dummy[:] = (127, 127, 127)
        self.update_progress(20)

        # Warm up OpenCV and Pillow
        _ = cv2.cvtColor(dummy, cv2.COLOR_BGR2RGB)
        self.update_progress(30)
        _ = Image.fromarray(dummy)
        self.update_progress(40)
        _ = apply_kelvin_temperature(dummy, 5000)
        self.update_progress(50)
        _ = apply_brightness(dummy, 1.0)
        self.update_progress(60)
        _ = apply_contrast(dummy, 1.0)
        self.update_progress(70)
        _ = adjust_saturation_rgb(dummy, 1.0)
        self.update_progress(80)
        for i in range(81, 91):
            self.update_progress(i)
        _ = apply_hsl_superfast(dummy, {'red': 0}, {'red': 0}, {'red': 0})
        self.update_progress(91)
        _ = apply_primary_calibration_rgb(dummy, 0, 0, 0, 1, 1, 1)
        self.update_progress(95)
        _ = apply_shadow_calibration_rgb(dummy, 0, 0, 0, 1, 1, 1)
        self.update_progress(100)
        _ = cv2.LUT(dummy, np.arange(256, dtype=np.uint8))  # warm up LUT

    
    # def update_progress(self, value):
    #     self.progress_bar.set(value)
    #     percent_text = f"{int(value)}%" #f"{int(value * 100)}%"
    #     self.progress_percent_label.configure(text=percent_text)

    def update_progress(self, value):
        self.progress_bar.set(value)
        percent = int(value)
        self.progress_percent_label.configure(text=f"{percent}%")

        # Green RGB: (0, 255, 0), Red RGB: (255, 0, 0)
        r = int(255 * (value / 100))        # Red increases with progress
        g = int(255 * (1 - value / 100))    # Green decreases with progress
        b = 0                               # No blue
        color = f"#{g:02x}{r:02x}{b:02x}"

        self.progress_bar.configure(progress_color=color)

    def show_info_window(self, text):
        self.info_window = ctk.CTkToplevel(self.root)
        self.info_window.title("Initializing")
        self.info_window.geometry("300x100")
        self.info_window.grab_set() # Block interaction with main window
        self.info_window.resizable(False, False)

        # Center the window
        self.root.update_idletasks()
        root_x = self.root.winfo_rootx()
        # print(' ----------- root_x ------------- ', root_x)
        root_y = self.root.winfo_rooty()
        # print(' ----------- root_y ------------- ', root_y)
        root_width = self.root.winfo_width()
        # print(' ----------- root_width ------------- ', root_width)
        root_height = self.root.winfo_height()
        # print(' ----------- root_height ------------- ', root_height)
        x = root_x + (root_width // 2) + 150
        # print(' ----------- X ------------- ', root_y)
        y = root_y + (root_height // 2) + 50
        # print(' ----------- Y ------------- ', root_y)
        self.info_window.geometry(f"+{x}+{y}")

        # Use CTkLabel with dark background
        label = ctk.CTkLabel(
            self.info_window,
            text=text,
            font=ctk.CTkFont(size=14),
            text_color="white" 
        )
        label.pack(expand=True, fill="both", padx=10, pady=10)

        # Create indeterminate progress bar
        self.progress_bar = ctk.CTkProgressBar(self.info_window, mode="indeterminate", width=200)
        self.progress_bar.pack(pady=10)
        self.progress_bar.start()

        self.progress_percent_label = ctk.CTkLabel(
        self.info_window, text="0%", text_color="white", font=("Arial", 12)
        )
        self.progress_percent_label.pack(pady=(0, 10))