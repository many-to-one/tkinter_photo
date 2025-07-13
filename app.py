import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import cv2
import numpy as np
from PIL import Image, ImageTk, ImageEnhance, ImageDraw
import math

import threading
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool, cpu_count

import rawpy
import colorsys

from adjustments.mains import *
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

from local_adjustments.gradient import *

from adjustments_c.brightness_c import apply_all_adjustments_c

from apply_section.apply_adjustments import apply_adjustments
# from apply_section.apply_adjustments_high_res import apply_adjustments_high_res


from info_windows.window_process import InfoWindow
from info_windows.init_window import InitWindow
from zoom.zoom import Zoom

# Theme
ctk.set_appearance_mode("Dark")


class HighMenu(ctk.CTkFrame):
    def __init__(self, master, width=300, height=570, corner_radius=0):
        super().__init__(master)


class RightSideBar(ctk.CTkFrame):
    def __init__(self, master, width=30, height=570, corner_radius=0):
        super().__init__(master)

        # self.right_menu.grid(row=1, column=0, sticky="w")


class ImageEditorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.root = root = self
        # self.slider_update_job = None

        self.title("Image Editor")
        self.geometry("1000x600")
        self.configure(bg="#212121")  # Set background color

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Image variables
        self.original_image = None
        self.small_image = None
        self.curve_base_image = None
        self.display_image = None
        self.high_res_result = None

        # Zoom logic
        self.zoom_level = 1.0  # Default 100%
        self.zoom_step = 0.1   # 10% per step

        # Zoom with buttons
        # self.root.bind('<Control-minus>', self.zoom_out)
        # self.root.bind('<Control-plus>', self.zoom_in)
        # self.root.bind('<Control-equal>', self.zoom_in)  # Handle Ctrl + = (some keyboards)

        self.height_menu = HighMenu(self, width=300, height=30, corner_radius=0)
        self.height_menu.grid(row=0, column=0, pady=0, sticky="we")

        self.right_menu = RightSideBar(self, width=30, height=570, corner_radius=0)
        self.right_menu.grid(row=1, column=0, sticky="w")

if __name__ == "__main__":
    app = ImageEditorApp()
    app.mainloop()