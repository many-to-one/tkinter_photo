import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import cv2
import numpy as np
from PIL import Image, ImageTk, ImageEnhance

import threading
from concurrent.futures import ThreadPoolExecutor

import rawpy

from adjustments.brightness import apply_brightness
from adjustments.contrast import apply_contrast
from adjustments.saturation import adjust_saturation_rgb
from adjustments.curve import *
from adjustments.shadows_lights import adjust_shadows_lights


class ImageEditorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Photo Editor - Tkinter Lightroom")
        self.geometry("1000x600")

        self.last_params = {
            # "brightness": None,
            # "contrast": 1.0,
            # "saturation": 0.0,
            # "shadow_factor": 1.0,
            # "light_factor": 1.0
        }  

        # Image variables
        self.original_image = None
        self.display_image = None
        self.cached_stages = {}  # Cache for each step

        self.executor = ThreadPoolExecutor(max_workers=1)

        # UI Setup
        self.setup_ui()

    def setup_ui(self): 
        self.image_panel = ctk.CTkLabel(self, text="", bg_color="black")
        self.image_panel.pack(side="left", padx=10, pady=10, expand=True, fill="both")

        # controls = ctk.CTkFrame(self, width=200)
        # controls.pack(side="right", fill="y", padx=0)

        self.controls_scroll = ctk.CTkScrollableFrame(self, width=200)
        self.controls_scroll.pack(side="right", fill="y", padx=0)

        # Use this as your new parent for sliders and other controls
        controls = self.controls_scroll

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

        # Sliders for adjustments
        self.brightness_slider = self.create_slider(controls, -100, 100, 0, self.update_image, "Brightness")
        self.contrast_slider = self.create_slider(controls, 0.1, 2.0, 1.0, self.update_image, "Contrast")
        self.shadow_slider = self.create_slider(controls, 0.5, 2.0, 1.0, self.update_image, "Shadows")
        self.light_slider = self.create_slider(controls, 0.5, 2.0, 1.0, self.update_image, "Lights")
        self.color_slider = self.create_slider(controls, 0.0, 2.0, 1.0, self.update_image, "Saturation")
        self.dehaze_slider = self.create_slider(controls, -2.0, 2.0, 0.0, self.update_image, "Dehaze")

        reset_btn = ctk.CTkButton(controls, text="Reset", command=self.reset_sliders)
        reset_btn.pack(pady=10)


    def create_slider(self, parent, from_, to, default, command, label_text):
        label = ctk.CTkLabel(parent, text=label_text)
        label.pack()

        slider = ctk.CTkSlider(parent, from_=from_, to=to, command=command)
        slider.set(default)
        slider.pack(pady=5)
        return slider


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




    # def update_image(self, _=None):
    #     if self.original_image is None:
    #         return
    #     threading.Thread(target=self.apply_adjustments).start()

    def update_image(self, _=None):
        if self.original_image is None:
            return
        self.executor.submit(self.apply_adjustments) 


    def apply_adjustments(self):
        img = self.original_image.copy()

        brightness = self.brightness_slider.get()
        contrast = self.contrast_slider.get()
        shadow_factor = self.shadow_slider.get()
        light_factor = self.light_slider.get()
        saturation = self.color_slider.get()
        dehaze = self.dehaze_slider.get()

        img = apply_brightness(img, brightness)
        img = apply_contrast(img, contrast)
        img = adjust_saturation_rgb(img, saturation)
        img = adjust_shadows_lights(img, shadow_factor, light_factor)
        img = self.dehaze_image(img, dehaze)

        # Curve
        lut = self.generate_lut()

        b, g, r = cv2.split(img)
        r = cv2.LUT(r, lut)
        g = cv2.LUT(g, lut)
        b = cv2.LUT(b, lut)
        img = cv2.merge((b, g, r))

        self.display_image = img
        self.show_image(self.display_image)


    def show_image(self, img):
        # Resize for display to improve performance
        resized = cv2.resize(img, (800, 600))
        img_rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        tk_img = ImageTk.PhotoImage(pil_img)

        self.image_panel.configure(image=tk_img)
        self.image_panel.image = tk_img


    def dehaze_image(self, img, strength):
        # if strength == 0:
        #     return img

        # lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        # l, a, b = cv2.split(lab)
        # print(' ------ dehaze_image ------', strength)

        # clahe = cv2.createCLAHE(clipLimit=2.0 + 4.0 * strength, tileGridSize=(8, 8))
        # cl = clahe.apply(l)

        # merged = cv2.merge((cl, a, b))
        # return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

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
