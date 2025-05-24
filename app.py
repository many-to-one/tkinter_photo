import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageEnhance
import numpy as np
import cv2
import threading

from adjustments.shadows_lights import adjust_shadows_lights

class ImageEditorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Photo Editor - Tkinter Lightroom")
        self.geometry("1000x600")

        self.original_image = None
        self.brightness_image = None
        self.contrast_image = None
        self.color_image = None
        self.shadow_light_image = None
        self.curve_image = None
        self.final_image = None

        self.setup_ui()

    def setup_ui(self):
        self.image_panel = ctk.CTkLabel(self, text="", bg_color="black")
        self.image_panel.pack(side="left", padx=10, pady=10, expand=True, fill="both")

        controls = ctk.CTkFrame(self, width=200)
        controls.pack(side="right", fill="y", padx=10)

        ctk.CTkButton(controls, text="Open Image", command=self.open_image).pack(pady=10)

        # Curve canvas
        self.canvas = tk.Canvas(controls, bg="black", width=256, height=256)
        self.canvas.pack(padx=20, pady=20)
        self.points = [(0, 255), (64, 192), (128, 128), (192, 64), (255, 0)]
        self.canvas.bind("<Button-1>", self.add_point)
        self.canvas.bind("<B1-Motion>", self.move_point)
        self.draw_curve()

        ctk.CTkButton(controls, text="Reset Curve", command=self.reset_curve).pack(pady=10)

        # Sliders
        self.brightness_slider = self.create_slider(controls, -100, 100, self.on_brightness_change)
        self.contrast_slider = self.create_slider(controls, 0.1, 2.0, self.on_contrast_change)
        self.shadow_slider = self.create_slider(controls, 0.5, 2.0, self.on_shadow_light_change)
        self.light_slider = self.create_slider(controls, 0.5, 2.0, self.on_shadow_light_change)
        self.color_slider = self.create_slider(controls, 0.0, 2.0, self.on_color_change)

        ctk.CTkButton(controls, text="Reset All", command=self.reset_all).pack(pady=10)

    def create_slider(self, parent, from_, to, command, default=0):
        slider = ctk.CTkSlider(parent, from_=from_, to=to, command=command)
        slider.set(default)
        slider.pack(pady=5)
        return slider

    def open_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.png *.jpeg *.cr2")])
        if path:
            img = Image.open(path).convert("RGB")
            self.original_image = np.array(img)
            self.process_all()
    
    def process_all(self):
        self.update_brightness()
        self.update_contrast()
        self.update_color()
        self.update_shadow_light()
        self.update_curve()
        self.compose_final_image()

    def on_brightness_change(self, _=None):
        self.update_brightness()
        self.compose_final_image()

    def on_contrast_change(self, _=None):
        self.update_contrast()
        self.compose_final_image()

    def on_color_change(self, _=None):
        self.update_color()
        self.compose_final_image()

    def on_shadow_light_change(self, _=None):
        self.update_shadow_light()
        self.compose_final_image()

    def update_brightness(self):
        factor = self.brightness_slider.get() / 100.0 + 1.0
        pil = Image.fromarray(self.original_image)
        enhanced = ImageEnhance.Brightness(pil).enhance(factor)
        self.brightness_image = np.array(enhanced)

    def update_contrast(self):
        factor = self.contrast_slider.get()
        pil = Image.fromarray(self.brightness_image)
        enhanced = ImageEnhance.Contrast(pil).enhance(factor)
        self.contrast_image = np.array(enhanced)

    def update_color(self):
        factor = self.color_slider.get()
        pil = Image.fromarray(self.contrast_image)
        enhanced = ImageEnhance.Color(pil).enhance(factor)
        self.color_image = np.array(enhanced)

    def update_shadow_light(self):
        self.shadow_light_image = adjust_shadows_lights(
            self.color_image,
            self.shadow_slider.get(),
            self.light_slider.get()
        )

    def update_curve(self):
        lut = self.generate_lut()
        r, g, b = cv2.split(self.shadow_light_image)
        r = cv2.LUT(r, lut)
        g = cv2.LUT(g, lut)
        b = cv2.LUT(b, lut)
        self.curve_image = cv2.merge((r, g, b))

    def compose_final_image(self):
        self.final_image = self.curve_image
        self.display_image = Image.fromarray(self.final_image)
        self.show_image(self.display_image)

    def show_image(self, pil_img):
        img_resized = pil_img.resize((500, 500))  # Resize for preview
        photo = ctk.CTkImage(light_image=img_resized, size=(500, 500))
        self.image_panel.configure(image=photo)
        self.image_panel.image = photo

    # === Curve logic ===

    def draw_curve(self):
        self.canvas.delete("all")
        self.points = sorted(self.points)
        for x, y in self.points:
            self.canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill="white")
        for i in range(len(self.points) - 1):
            self.canvas.create_line(*self.points[i], *self.points[i + 1], fill="cyan", width=2)
        if self.original_image is not None:
            self.update_curve()
            self.compose_final_image()

    def generate_lut(self):
        xs, ys = zip(*sorted(self.points))
        ys = [255 - y for y in ys]
        lut = np.interp(np.arange(256), xs, ys)
        return np.clip(lut, 0, 255).astype(np.uint8)

    def add_point(self, event):
        if event.state & 0x0004:
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

    def reset_all(self):
        self.brightness_slider.set(0)
        self.contrast_slider.set(1.0)
        self.shadow_slider.set(1.0)
        self.light_slider.set(1.0)
        self.color_slider.set(1.0)
        self.reset_curve()
        self.process_all()

    # ======= External Functions =======

    # def adjust_shadows_lights(img, shadow_factor=1.0, light_factor=1.0):
    #     lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
    #     l, a, b = cv2.split(lab)
    #     l_mod = fast_adjust_l_channel(l, shadow_factor, light_factor)
    #     adjusted = cv2.merge((l_mod, a, b))
    #     return cv2.cvtColor(adjusted, cv2.COLOR_LAB2RGB)

    # from numba import njit

    # @njit
    # def fast_adjust_l_channel(l, shadow_factor, light_factor):
    #     l_mod = l.astype(np.float32)
    #     for i in range(l.shape[0]):
    #         for j in range(l.shape[1]):
    #             val = l[i, j] / 255.0
    #             if val < 0.5:
    #                 l_mod[i, j] *= shadow_factor
    #             else:
    #                 l_mod[i, j] *= light_factor
    #     return np.clip(l_mod, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    app = ImageEditorApp()
    app.mainloop()
