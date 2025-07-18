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

from menu.top_menu import TopMenu
from menu.left_menu import LeftSideBar
from menu.right_menu import RightSideBar
from menu.image_panel import ImagePanel

# Theme
ctk.set_appearance_mode("Dark")




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

        
        """      
            Example grid layout:
            self.grid_rowconfigure(0, weight=1)
            self.grid_rowconfigure(1, weight=30)
            → Total weight = 1 + 30 = 31
            → Row 1 gets 30/31 ≈ 96.8% of the height
            → Row 0 gets 1/31 ≈ 3.2%

        """
        # ← critical!
        # Only row 1 is stretchable to get max height of left_menu
        self.grid_rowconfigure(0, weight=0)  # top_menu
        self.grid_rowconfigure(1, weight=1)  # left_menu

        self.grid_columnconfigure(2, weight=0)  # right_menu fixed width
        self.grid_rowconfigure(1, weight=1)     # row for content should grow

        self.top_menu = TopMenu(self, height=35)
        self.top_menu.grid(row=0, column=0, columnspan=3, pady=0, sticky="wne")

        self.left_menu = LeftSideBar(self, width=35)
        self.left_menu.grid(row=1, column=0, sticky="nsw")  # ← stretch vertically + stick left

        self.image_panel = ImagePanel(self)
        self.image_panel.grid(row=1, column=1, sticky="nsew")  # Full center area
        # Label to display the image inside the panel
        self.image_label = ctk.CTkLabel(self.image_panel, text="")
        self.image_label.pack(expand=True, fill="both")

        self.right_menu = RightSideBar(self, width=300)
        self.right_menu.grid(row=1, column=2, sticky="nse")

        # self.image_panel = ctk.CTkLabel(self, text="", bg_color="#333333")
        # self.image_panel.pack(side="left", expand=True, fill="both")

        # Zoom with the mouse wheel
        self.image_panel.bind("<MouseWheel>", self.image_panel.on_mousewheel)  # Windows
        self.image_panel.bind("<Button-4>", self.image_panel.on_mousewheel)    # Linux
        self.image_panel.bind("<Button-5>", self.image_panel.on_mousewheel)

    
    def refresh_image(self):
        # Step 1: Apply base adjustments
        base_adjusted = self.apply_adjustments()

        # Step 2: Apply gradient effects on top
        final_image = self.gradients_controller.apply_gradients(
            base_adjusted.copy(),  # Don't mutate base
            self.gradients
        )

        # Step 3: Draw gradient edges
        overlayed = self.gradients_controller.draw_gradient_edges(final_image.copy(), self.gradients)

        # Step 4: Show the final result
        self.display_image = final_image
        self.show_image(self.display_image)



    

if __name__ == "__main__":
    app = ImageEditorApp()
    app.mainloop()