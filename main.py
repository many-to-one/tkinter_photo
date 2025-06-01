import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import cv2
import numpy as np
from PIL import Image, ImageTk, ImageEnhance

import threading
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool, cpu_count

import rawpy

from adjustments.brightness import apply_brightness
from adjustments.contrast import apply_contrast
from adjustments.saturation import adjust_saturation_rgb
from adjustments.curve import *
from adjustments.shadows_lights import adjust_shadows_lights
from adjustments.white_balance import *
from adjustments.dehaze import dehaze_effect
from adjustments.fog import fog_effect
from adjustments.hsl import *
from adjustments.tiles import *

# Theme
ctk.set_appearance_mode("Dark")


class ImageEditorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.root = root = self
        self.slider_update_job = None

        self.title("Image Editor")
        self.geometry("1000x600")
        self.configure(bg="#212121")  # Set background color

        # Image variables
        self.original_image = None
        self.display_image = None

        self.preview_image = None
        self.preview_scale = 0.1  # Or dynamically calculate to fit screen

        self.executor = ThreadPoolExecutor(max_workers=1)

        # UI Setup
        self.setup_ui()



    def setup_ui(self): 
        self.image_panel = ctk.CTkLabel(self, text="", bg_color="#333333")
        self.image_panel.pack(side="left", expand=True, fill="both")

        controls_scroll = ctk.CTkScrollableFrame(self, width=300, fg_color="#212121")
        controls_scroll.pack(side="right", fill="y")

        # Use this as the parent for accordion sections
        controls = controls_scroll

        open_btn = ctk.CTkButton(controls, text="Open Image", command=self.open_image)
        open_btn.pack(pady=10)

        # Curve
        self.canvas = tk.Canvas(controls, bg="black", width=256, height=256)
        self.canvas.pack(padx=20, pady=20)
        # Control points (x in [0,255], y in [0,255])
        self.points = [(0, 255), (64, 192), (128, 128), (192, 64), (255, 0)]

        self.canvas.bind("<Button-1>", self.add_point)
        self.canvas.bind("<B1-Motion>", self.move_point)
        self.draw_curve()

        self.canvas.bind("<Button-1>", self.add_point)
        self.canvas.bind("<B1-Motion>", self.move_point)

        reset_curve_btn = ctk.CTkButton(controls, text="Reset Curve", command=self.reset_curve)
        reset_curve_btn.pack(pady=10)

        # End curve

        # Accordion sections

        # Sliders for adjustments

        # White balance accordion section
        white_balance_section = self.create_accordion_section(controls, "White Balance")
        self.temperature_slider = self.create_slider(white_balance_section, 1000, 10000, 6500, lambda value: self.update_image('temperature', value), "Temperature (K)")
        self.tint_slider = self.create_slider(white_balance_section, -150, 150, 0, lambda value: self.update_image('tint', value), "Tint")

        # self.temp_slider = self.create_slider(white_balance_section, -100, 100, 0, self.update_image, "Temperature")
        # self.tint_slider = self.create_slider(white_balance_section, -100, 100, 0, self.update_image, "Tint")

        # Ton sliders inside tone_section
        tone_section = self.create_accordion_section(controls, "Tone")
        self.brightness_slider = self.create_slider(tone_section, -100, 100, 0, lambda value: self.update_image('brightness', value), "Brightness")
        self.contrast_slider = self.create_slider(tone_section, 0.1, 2.0, 1.0, lambda value: self.update_image('bontrast', value), "Contrast")
        self.shadow_slider = self.create_slider(tone_section, 0.5, 2.0, 1.0, lambda value: self.update_image('shadows', value), "Shadows")
        self.light_slider = self.create_slider(tone_section, 0.5, 2.0, 1.0, lambda value: self.update_image('lights', value), "Lights")
        self.color_slider = self.create_slider(tone_section, 0.0, 2.0, 1.0, lambda value: self.update_image('saturation', value), "Saturation")
        self.dehaze_slider = self.create_slider(tone_section, -2.0, 2.0, 0.0, lambda value: self.update_image('dehaze', value), "Dehaze")
        self.fog_slider = self.create_slider(tone_section, -2.0, 2.0, 0.0, lambda value: self.update_image('fog', value), "Fog")


        # HSL
        self.hsl_section = self.create_accordion_section(controls, "HSL")

        self.hue_sliders = {}
        self.sat_sliders = {}
        self.lum_sliders = {}

        colors = ["Red", "Orange", "Yellow", "Green", "Aqua", "Blue", "Purple", "Magenta"]
        for color in colors:
            self.hue_sliders[color] = self.create_slider(self.hsl_section, -180, 180, 0, lambda value: self.update_image(f"hue_adj", value), f"{color} Hue")
            self.sat_sliders[color] = self.create_slider(self.hsl_section, -1.0, 1.0, 0, lambda value: self.update_image(f"sat_adj", value), f"{color} Saturation")
            self.lum_sliders[color] = self.create_slider(self.hsl_section, -1.0, 1.0, 0, lambda value: self.update_image(f"lum_adj", value), f"{color} Luminance")




        reset_btn = ctk.CTkButton(controls, text="Reset", command=self.reset_sliders)
        reset_btn.pack(pady=10)


    def toggle_section(self, frame):
        if frame.winfo_viewable():
            frame.pack_forget()
        else:
            frame.pack(fill="x", padx=10, pady=5)


    def create_slider(self, parent, from_, to, default, command, text):
        frame = ctk.CTkFrame(parent)  # Optional: wrap each slider in a frame
        frame.pack(fill="x", pady=4)

        label = ctk.CTkLabel(frame, text=text)
        label.pack(anchor="w")

        slider = ctk.CTkSlider(frame, from_=from_, to=to, command=command)
        slider.set(default)
        print(f' ----------- slider {text} ------------- ', slider.get())
        slider.pack(fill="x")

        return slider

    def create_accordion_section(self, parent, title):
        section_frame = ctk.CTkFrame(parent)
        section_frame.pack(fill="x", padx=5, pady=5)

        content = ctk.CTkFrame(section_frame)

        toggle_btn = ctk.CTkButton(section_frame, text=title, fg_color="#333333", command=lambda: self.toggle_section(content))
        toggle_btn.pack(fill="x")

        return content



    def open_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.png *.jpeg *.tiff *.cr2")])
        
        if path.lower().endswith(".cr2"):  # RAW format handling
            raw = rawpy.imread(path)
            rgb = raw.postprocess()
            self.original_image = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        
        elif path.lower().endswith(".tiff"):  # TIFF format handling
            pil_img = Image.open(path)
            self.original_image = np.array(pil_img)  # Convert Pillow image to NumPy
        
        else:  # Standard formats
            self.original_image = cv2.imread(path, cv2.IMREAD_UNCHANGED)

        if self.original_image is None:
            print("Error loading image!")
            return

        self.display_image = self.original_image.copy()
        self.show_image(self.display_image)


    def calculate_preview_scale(self, image):
        max_width, max_height = 1000, 800  # Tune to your GUI window size
        h, w = image.shape[:2]
        scale = min(max_width / w, max_height / h, 1.0)  # Ensure it's never scaled up
        return scale



    # def update_image(self, _=None):
    #     if self.original_image is None:
    #         return
    #     threading.Thread(target=self.apply_adjustments).start()

    def update_image(self, tipo, _=None):
    # def update_image(self, tipo,):
        if self.original_image is None:
            return
        self.executor.submit(self.apply_adjustments, tipo) 






    def apply_adjustments(self, tipo, high_res=False):

        print('----------- tipo ------------', tipo)
        img = self.original_image.copy()
        # img = self.original_image if high_res else self.display_image.copy()

        
        brightness = self.brightness_slider.get()
        contrast = self.contrast_slider.get()
        shadow_factor = self.shadow_slider.get()
        light_factor = self.light_slider.get()
        saturation = self.color_slider.get()
        dehaze = self.dehaze_slider.get()
        fog = self.fog_slider.get()


        # White balance
        temperature = int(self.temperature_slider.get())
        tint = int(self.tint_slider.get())

        # # Eyedropper
        # if hasattr(self, 'eyedropper_pixel') and self.eyedropper_pixel is not None:
        #     img = apply_white_balance_eyedropper(img, self.eyedropper_pixel)

        # Kelvin-based temperature adjustment
        img = apply_kelvin_temperature(img, temperature)
        img = apply_tint_shift(img, tint)

        img = apply_brightness(img, brightness)
        img = apply_contrast(img, contrast)
        img = adjust_saturation_rgb(img, saturation)
        img = adjust_shadows_lights(img, shadow_factor, light_factor)
        img = self.dehaze_effect(img, dehaze)
        img = self.fog_effect(img, fog)

        # Curve
        lut = self.generate_lut()

        b, g, r = cv2.split(img)
        r = cv2.LUT(r, lut)
        g = cv2.LUT(g, lut)
        b = cv2.LUT(b, lut)
        img = cv2.merge((b, g, r))

        hue_adj = {color: slider.get() for color, slider in self.hue_sliders.items()}
        sat_adj = {color: slider.get() for color, slider in self.sat_sliders.items()}
        lum_adj = {color: slider.get() for color, slider in self.lum_sliders.items()}

        img = apply_hsl_superfast(img, hue_adj, sat_adj, lum_adj)

        # print(' ----------- adjustment dimensions --------------', img.shape)

        self.display_image = img
        self.show_image(self.display_image)







    # def apply_adjustments(self, tipo, high_res=False):

    #     print('----------- tipo ------------', tipo)
    #     img = self.original_image.copy()
    #     # img = self.original_image if high_res else self.display_image.copy()

    #     brightness = self.brightness_slider.get()
    #     contrast = self.contrast_slider.get()
    #     shadow_factor = self.shadow_slider.get()
    #     light_factor = self.light_slider.get()
    #     saturation = self.color_slider.get()
    #     dehaze = self.dehaze_slider.get()
    #     fog = self.fog_slider.get()

    #     # HSL
    #     # hue_adj = {color: slider.get() for color, slider in self.hue_sliders.items()}
    #     # sat_adj = {color: slider.get() for color, slider in self.sat_sliders.items()}
    #     # lum_adj = {color: slider.get() for color, slider in self.lum_sliders.items()}

    #     # img = apply_hsl_superfast(img, hue_adj, sat_adj, lum_adj)

    #     # # 1. Read HSL slider values as dictionaries
    #     # hue_adj_dict = {color: self.hue_sliders[color].get() for color in self.hue_sliders}
    #     # sat_adj_dict = {color: self.sat_sliders[color].get() for color in self.sat_sliders}
    #     # lum_adj_dict = {color: self.lum_sliders[color].get() for color in self.lum_sliders}

    #     # # Create hue LUT once and reuse
    #     # # Order of bands must match the LUT creation!
    #     # band_order = ['Red', 'Orange', 'Yellow', 'Green', 'Aqua', 'Blue', 'Purple', 'Magenta']

    #     # # 3. Convert to arrays
    #     # hue_adj = np.array([hue_adj_dict.get(c, 0) for c in band_order], dtype=np.float32)
    #     # sat_adj = np.array([sat_adj_dict.get(c, 0) for c in band_order], dtype=np.float32)
    #     # lum_adj = np.array([lum_adj_dict.get(c, 0) for c in band_order], dtype=np.float32)

    #     # # Convert to HLS
    #     # hls = cv2.cvtColor(img, cv2.COLOR_BGR2HLS).astype(np.float32)

    #     # # Apply fast HSL logic
    #     # hue_lut = create_hue_band_lut()
    #     # adjusted_hls = apply_hsl_core_lut(hls, hue_lut, hue_adj, sat_adj, lum_adj)

    #     # # Back to BGR
    #     # img = cv2.cvtColor(adjusted_hls.astype(np.uint8), cv2.COLOR_HLS2BGR)



    #     # White balance
    #     temperature = int(self.temperature_slider.get())
    #     tint = int(self.tint_slider.get())

    #     # # Eyedropper
    #     # if hasattr(self, 'eyedropper_pixel') and self.eyedropper_pixel is not None:
    #     #     img = apply_white_balance_eyedropper(img, self.eyedropper_pixel)

    #     # Kelvin-based temperature adjustment
    #     img = apply_kelvin_temperature(img, temperature)
    #     img = apply_tint_shift(img, tint)

    #     img = apply_brightness(img, brightness)
    #     img = apply_contrast(img, contrast)
    #     img = adjust_saturation_rgb(img, saturation)
    #     img = adjust_shadows_lights(img, shadow_factor, light_factor)
    #     img = self.dehaze_effect(img, dehaze)
    #     img = self.fog_effect(img, fog)

    #     # Curve
    #     lut = self.generate_lut()

    #     b, g, r = cv2.split(img)
    #     r = cv2.LUT(r, lut)
    #     g = cv2.LUT(g, lut)
    #     b = cv2.LUT(b, lut)
    #     img = cv2.merge((b, g, r))

    #     hue_adj = {color: slider.get() for color, slider in self.hue_sliders.items()}
    #     sat_adj = {color: slider.get() for color, slider in self.sat_sliders.items()}
    #     lum_adj = {color: slider.get() for color, slider in self.lum_sliders.items()}

    #     img = apply_hsl_superfast(img, hue_adj, sat_adj, lum_adj)

    #     # print(' ----------- adjustment dimensions --------------', img.shape)

    #     self.display_image = img
    #     self.show_image(self.display_image)







    # def apply_adjustments(self, tipo, high_res=False):
    #     img = self.original_image.copy()

    #     hue_adj = {color: slider.get() for color, slider in self.hue_sliders.items()}
    #     sat_adj = {color: slider.get() for color, slider in self.sat_sliders.items()}
    #     lum_adj = {color: slider.get() for color, slider in self.lum_sliders.items()}

    #     # img = apply_hsl_superfast(img, hue_adj, sat_adj, lum_adj)

    #     adjustments = {}
    #     adjustments['temperature'] = int(self.temperature_slider.get())
    #     adjustments['tint'] = int(self.tint_slider.get())
    #     adjustments['brightness'] = self.brightness_slider.get()
    #     adjustments['contrast'] = self.contrast_slider.get()
    #     adjustments['shadow_factor'] = self.shadow_slider.get()
    #     adjustments['light_factor'] = self.light_slider.get()
    #     adjustments['saturation'] = self.color_slider.get()
    #     adjustments['dehaze'] = self.dehaze_slider.get()
    #     adjustments['fog'] = self.fog_slider.get() 
    #     adjustments['hue_adj'] = hue_adj 
    #     adjustments['sat_adj'] = sat_adj
    #     adjustments['lum_adj'] = lum_adj

    #     for key in adjustments.keys():
    #         if key == tipo:
    #             print('----------- adjustments key ---------------', tipo)
    #             with ThreadPoolExecutor(max_workers=8) as executor:
    #                 tiles = list(executor.map(lambda tile: process_tile(tile, tipo), tiles))

    #                 tiles = split_image_into_tiles(img)

    #                 img = merge_tiles_back(tiles)

    #                 self.display_image = img
    #                 self.show_image(self.display_image)

                    
    #                 """
    #                 pridumat funkcyju, update changes gdie nużno perezapisywać tiekuszczeje izobrażenije 
    #                 s nowymi izmienienijami, skażem jesli my chotim dobawic brightness to pierezapisywajem 
    #                 izobr. s brightness. Potom chotimdobawić lightness, to dobowliajem uze k periezap. izobr,
    #                 gdzie uże jesć nowoje britness i t.d.
    #                 """

    #     print('----------- apply_adjustments sat_adj ---------------', adjustments['sat_adj'])
    #     print('----------- apply_adjustments lum_adj ---------------', adjustments['lum_adj'])

    #     # Split into tiles
    #     # tiles = split_image_into_tiles(img)

    #     # Process tiles in parallel
    #     # with ThreadPoolExecutor(max_workers=8) as executor:
    #     #     tiles = list(executor.map(lambda tile: process_tile(tile, adjustments), tiles))

    #     # with Pool(processes=cpu_count()) as pool:
    #     #     tiles = pool.starmap(process_tile, [(tile, adjustments) for tile in tiles])

    #         # print([type(t) for t in tiles])

    #     # Merge back
    #     # img = merge_tiles_back(tiles)

    #     # self.display_image = img
    #     # self.show_image(self.display_image)





##############################################################################################################################################
############################################################ === DEHAZE === ##################################################################
##############################################################################################################################################

    def dehaze_effect(self, img, strength):
        if strength == 0:
            return img

        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        # print(' ------ dehaze_image ------', strength)

        clahe = cv2.createCLAHE(clipLimit=2.0 + 4.0 * strength, tileGridSize=(8, 8))
        cl = clahe.apply(l)

        merged = cv2.merge((cl, a, b))
        return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

##############################################################################################################################################
############################################################### === FOG === ##################################################################
##############################################################################################################################################

    def fog_effect(self, img, strength):

        """
        Adds a fog effect by blending the image with a white layer.
        fog_intensity: float between 0 (no fog) and 2.0 (max fog)
        """
        fog_intensity = np.clip(strength, 0.0, 2.0)

        # Create a white image
        fog_color = np.full_like(img, 255)

        # Blend original with white
        blend_strength = min(strength / 2.0, 1.0)
        fogged = cv2.addWeighted(img, 1 - blend_strength, fog_color, blend_strength, 0)

        # Optional: reduce contrast slightly
        if strength > 0.1:
            fogged = apply_contrast(fogged, 1.0 - (strength * 0.15))  # adjust as needed

        return fogged


    def show_image(self, img):
        # Resize for display to improve performance
        resized = cv2.resize(img, (800, 600))
        img_rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        tk_img = ImageTk.PhotoImage(pil_img)

        self.image_panel.configure(image=tk_img)
        self.image_panel.image = tk_img



    # === Curve === #

    def apply_curve_only(self):
        if self.display_image is None:
            return

        img = self.display_image.copy()

        # Ensure uint8 RGB
        if img.dtype != np.uint8:
            img = np.clip(img, 0, 255).astype(np.uint8)

        lut = self.generate_lut()

        b, g, r = cv2.split(img)
        r = cv2.LUT(r, lut)
        g = cv2.LUT(g, lut)
        b = cv2.LUT(b, lut)
        img = cv2.merge((b, g, r))

        self.show_image(img)

    def draw_curve(self):
        self.canvas.delete("all")
        self.points = sorted(self.points)
        for x, y in self.points:
            self.canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill="white")
        for i in range(len(self.points) - 1):
            self.canvas.create_line(*self.points[i], *self.points[i + 1], fill="cyan", width=2)

        # Only apply curve now (fast update)
        if self.display_image is not None:
            self.apply_curve_only()
            # threading.Thread(target=self.apply_adjustments).start()


    def generate_lut(self):
        xs, ys = zip(*sorted(self.points))
        ys = [255 - y for y in ys]  # Invert to match brightness
        lut = np.interp(np.arange(256), xs, ys)
        return np.clip(lut, 0, 255).astype(np.uint8)

    def add_point(self, event):
        if event.state & 0x0004:  # Ctrl key on Windows/Linux
            self.points.append((event.x, event.y))
            self.draw_curve()

    def move_point(self, event):
        closest = min(self.points, key=lambda p: abs(p[0] - event.x))
        self.points.remove(closest)
        self.points.append((event.x, event.y))
        self.draw_curve()

    def reset_curve(self):
        self.points = [(0, 255), (64, 192), (128, 128), (192, 64), (255, 0)]
        self.draw_curve()
    
    # === End Curve === #




    def reset_sliders(self):
        self.brightness_slider.set(0)
        self.contrast_slider.set(1.0)
        self.color_slider.set(1.0)
        self.shadow_slider.set(1.0)
        self.light_slider.set(1.0)
        self.update_image()

if __name__ == "__main__":
    app = ImageEditorApp()
    app.mainloop()
