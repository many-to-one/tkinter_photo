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

# from adjustments.mains import *
# from adjustments.brightness import apply_brightness
# from adjustments.contrast import apply_contrast
# from adjustments.saturation import adjust_saturation_rgb
# from adjustments.curve import *
# from adjustments.shadows_lights import adjust_shadows_lights
# from adjustments.white_balance import *
# from adjustments.dehaze_effect import dehaze_effect
# from adjustments.fog_effect import fog_effect
# from adjustments.hsl import *
# from adjustments.tiles import *
# from adjustments.camera_calibration import *

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

        # Gradients
        self.gradients_controller = GradientController(self)
        self.gradients = []
        self.sliders = {}
        self.gradient_panel_visible = False

        self.root.bind("<Button-3>", self.gradients_controller.delete_gradient)  # Right click
        self.root.bind("<Button-1>", self.gradients_controller.on_mouse_down)                 # Left click
        self.root.bind("<Double-Button-1>", self.gradients_controller.on_mouse_double_click)
        self.root.bind("<B1-Motion>", self.gradients_controller.on_mouse_drag)                # Drag with button 1
        self.root.bind("<ButtonRelease-1>", self.gradients_controller.on_mouse_up)            # Release
        self.root.bind("<Motion>", self.gradients_controller.on_mouse_move)

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
        self.grid_columnconfigure(1, weight=0)  # gradient_panel (toggleable)
        self.grid_rowconfigure(1, weight=1)  # left_menu
        self.grid_columnconfigure(2, weight=0)  # right_menu fixed width
        self.grid_rowconfigure(1, weight=1)     # row for content should grow

        self.top_menu = TopMenu(self, height=35)
        self.top_menu.grid(row=0, column=0, columnspan=3, pady=0, sticky="wne")

        self.left_menu = LeftSideBar(self, width=35)
        self.left_menu.grid(row=1, column=0, sticky="nsw")  # ← stretch vertically + stick left

        self.image_panel = ImagePanel(self)
        self.image_panel.grid(row=1, column=0)  
        # Label to display the image inside the panel
        self.image_label = ctk.CTkLabel(self.image_panel, text="", bg_color="#333333")
        self.image_label.pack(side="left", expand=True, fill="both")

        self.right_menu = RightSideBar(self, width=300)
        self.right_menu.grid(row=1, column=2, sticky="nse")

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
        self.image_panel.show_image(self.display_image)


    # Normalize temperature slider from 1000–10000 with 6500 neutral
    def get_normalized_temperature(self):
        kelvin = self.right_menu.temperature_slider.get()
        return (kelvin - 6500) / 35.0  # scale it to -157 to +100

    def get_normalized_tint(self):
        return self.right_menu.tint_slider.get() / 1.0  # tint range is already -150 to +150



    def apply_adjustments(self, tipo=None, value=None, high_res=False):

        img = self.small_image.copy()

        # Tone
        brightness = self.right_menu.brightness_slider.get()
        contrast = self.right_menu.contrast_slider.get()
        shadow_factor = self.right_menu.shadow_slider.get()
        light_factor = self.right_menu.light_slider.get()
        saturation = self.right_menu.color_slider.get()
        dehaze = self.right_menu.dehaze_slider.get()
        fog = self.right_menu.fog_slider.get()

        # White balance
        temperature = self.get_normalized_temperature()
        tint = self.get_normalized_tint()


        hue_adj = {color: slider.get() for color, slider in self.right_menu.hue_sliders.items()}
        sat_adj = {color: slider.get() for color, slider in self.right_menu.sat_sliders.items()}
        lum_adj = {color: slider.get() for color, slider in self.right_menu.lum_sliders.items()}

        # print('----------- hue_adj ------------', hue_adj)
        # print('----------- sat_adj ------------', sat_adj)
        # print('----------- lum_adj ------------', lum_adj)

        primary_hue = {
            "Red": self.right_menu.primary_hue_sliders["Red"].get(),
            "Green": self.right_menu.primary_hue_sliders["Green"].get(),
            "Blue": self.right_menu.primary_hue_sliders["Blue"].get(),
        }
        primary_sat = {
            "Red": self.right_menu.primary_sat_sliders["Red"].get(),
            "Green": self.right_menu.primary_sat_sliders["Green"].get(),
            "Blue": self.right_menu.primary_sat_sliders["Blue"].get(),
        }

        # print(' ----------- primary_hue ------------ ', primary_hue)
        # print(' ----------- primary_sat ------------ ', primary_sat)


        shadows_tint = self.right_menu.shadows_tint.get()
        # print(' ----------- shadows_tint ------------ ', shadows_tint)


        img = apply_all_adjustments_c(
            img,
            brightness, contrast, saturation,
            shadow_factor, light_factor,
            temperature, tint,
            dehaze, fog,
            [hue_adj[color] for color in ["Red", "Orange", "Yellow", "Green", "Aqua", "Blue", "Purple", "Magenta"]],
            [sat_adj[color] for color in ["Red", "Orange", "Yellow", "Green", "Aqua", "Blue", "Purple", "Magenta"]],
            [lum_adj[color] for color in ["Red", "Orange", "Yellow", "Green", "Aqua", "Blue", "Purple", "Magenta"]],
            shadows_tint,
            primary_hue["Red"], primary_hue["Green"], primary_hue["Blue"],
            primary_sat["Red"], primary_sat["Green"], primary_sat["Blue"]
        )


        # Curve
        self.curve_base_image = img.copy()

        lut = self.right_menu.generate_lut()

        b, g, r = cv2.split(img)
        r = cv2.LUT(r, lut)
        g = cv2.LUT(g, lut)
        b = cv2.LUT(b, lut)
        img = cv2.merge((b, g, r))

        # self.display_image = img
        # self.show_image(self.display_image)

        return img

    # === Curve === #

    def apply_curve_only(self):
        if self.curve_base_image is None:
            img = self.small_image.copy()
            # return
        else:

        # img = self.original_image.copy()
            img = self.curve_base_image.copy()

        # Ensure uint8 RGB
        if img.dtype != np.uint8:
            img = np.clip(img, 0, 255).astype(np.uint8)

        lut = self.right_menu.generate_lut()

        b, g, r = cv2.split(img)
        r = cv2.LUT(r, lut)
        g = cv2.LUT(g, lut)
        b = cv2.LUT(b, lut)
        img = cv2.merge((b, g, r))
        # self.cached_image['img'] = img

        self.display_image = img
        self.image_panel.show_image(self.display_image)


    # ---------------------------------------------------------------------------------- #
    # Gradient                                                    #
    # ---------------------------------------------------------------------------------- #

    def gradient_sliders(self):

        if hasattr(self, 'slider_frame') and self.slider_frame.winfo_exists():
            self.slider_frame.destroy()

        self.slider_frame = ctk.CTkFrame(self, width=200)
        self.slider_frame.grid(row=1, column=0, sticky="nsw", pady=(0, 10), padx=(40, 0))

        # Close button inside slider_frame (top-right)
        close_button = ctk.CTkButton(
            self.slider_frame,
            text="X",
            width=25,
            height=25,
            fg_color="red",
            hover_color="#cc0000",
            command=self.close_gradient_panel
        )
        close_button.place(relx=1.0, rely=0.0, anchor="ne", x=-5, y=5)  # Place in top-right corner


        for name in ['brightness', 'contrast', 'temperature', 'tint', 'strength', "rotate"]:
            label = ctk.CTkLabel(self.slider_frame, text=name.title())
            label.pack(pady=(5, 0), anchor='w')

            var = ctk.DoubleVar()

            if name == 'temperature':
                from_, to_, default = -1.0, 1.0, 0.0
            elif name == 'strength':
                from_, to_, default = 0.0, 1.0, 1.0
            elif name == 'rotate':
                from_, to_, default = 0.0, 180.0, 0.0
            else:
                from_, to_, default = -1.0, 1.0, 0.0

            slider = ctk.CTkSlider(
                self.slider_frame,
                from_=from_,
                to=to_,
                variable=var,
                command=lambda v, n=name: self.update_gradient_changes(n, float(v))
            )
            slider.set(default)
            slider.pack(fill='x', padx=10, pady=(0, 10))
            self.sliders[name] = (slider, var)


    def add_gradient(self):

        print(' --------------------- len(self.gradients) ------------------', len(self.gradients))
        self.gradients_controller.clear_sliders()
        gradient_index = len(self.gradients)
        start = (0, 0)
        end = (2000, 300)
        angle = 0.0
        cx = (start[0] + end[0]) // 2
        cy = (start[1] + end[1]) // 2
        handle = self.gradients_controller.calculate_rotation_handle(cx, cy, angle)

        active_gradient = 0

        print('Adding new gradient in self.gradients:', self.gradients)

        for g in self.gradients:
            # print('Checking existing gradient:', g)
            if g["active"]:
                active_gradient = 1
                # self.gradients_controller.load_gradient_to_sliders(g)
                print('Gradient already active, skipping creation')
                # self.gradient_sliders()
                # self.refresh_image()
                break
            # g["active"] = False
        if active_gradient == 0:
            self.gradients.append({
                "gradient_index": gradient_index,
                "active": True,
                "start": start,
                "end": end,
                # ---
                "center": (cx, cy),
                "height_top": 100,
                "height_bottom": 100,
                # ---
                "angle": angle,
                "handle": handle,
                "effects": {...},
                "brightness": 0.0,
                "contrast": 0.0,
                "temperature": 0.0,
                "tint": 0.0,
                # "saturation": 1.0,
                # "dehaze": 0.0,
                # "fog": 0.0,
                # "shadows": 1.0,
                # "lights": 1.0,
                # "hsl": {
                #     "Red": {"hue": 0.0, "sat": 1.0, "lum": 1.0},
                #     "Orange": {"hue": 0.0, "sat": 1.0, "lum": 1.0},
                #     "Yellow": {"hue": 0.0, "sat": 1.0, "lum": 1.0},
                #     "Green": {"hue": 0.0, "sat": 1.0, "lum": 1.0},
                #     "Aqua": {"hue": 0.0, "sat": 1.0, "lum": 1.0},
                #     "Blue": {"hue": 0.0, "sat": 1.0, "lum": 1.0},
                #     "Purple": {"hue": 0.0, "sat": 1.0, "lum": 1.0},
                #     "Magenta": {"hue": 0.0, "sat": 1.0, "lum": 1.0},
                # },
                # "calibration": {
                #     "shadows_tint": 0.0,
                #     "Red": {"hue": 0.0, "sat": 1.0},
                #     "Green": {"hue": 0.0, "sat": 1.0},
                #     "Blue": {"hue": 0.0, "sat": 1.0},
                # }
            })

            # Show the sliders for the new gradients
            self.gradient_sliders()


            self.refresh_image()

            print(' --------------------- add_gradient ------------------', self.gradients)



    def update_gradient_changes(self, name, value):
        print(' --------------------- update_gradient_changes ------------------', name, value)

        active_gradient = next((g for g in self.gradients if g["active"]), None)
        if not active_gradient:
            return

        active_gradient[name] = value

        if name == "rotate":
            self.gradients_controller.update_gradient_rotation(active_gradient)

        self.refresh_image() 



    def close_gradient_panel(self):
        print(" **************** Closing gradient panel **************** ", self.gradients)
        for g in self.gradients:
            g["active"] = False
        try:
            self.gradient_panel_visible = False
            if hasattr(self, 'slider_frame') and self.slider_frame.winfo_exists():
                self.slider_frame.destroy()
            print("Gradient panel forcefully hidden.")
        except Exception as e:
            print("Can't close the panel:", e)


    def open_gradient_panel(self):
        if not self.gradient_panel_visible:
            # self.slider_frame.grid()
            self.gradient_panel_visible = True
            self.add_gradient() 
            print(" **************** Gradient panel shown **************** ")
        else:
            print(" **************** Gradient panel already visible, skipping creation **************** ")
            self.refresh_image()





    

if __name__ == "__main__":
    app = ImageEditorApp()
    app.mainloop()