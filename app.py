import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk, ImageEnhance
import cv2
import numpy as np
from io import BytesIO
import rawpy
import threading

class ImageEditorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Photo Editor - Tkinter Lightroom")
        self.geometry("1000x600")

        # Image variables
        self.original_image = None
        self.display_image = None

        # Layout
        self.setup_ui()

    def setup_ui(self):
        self.image_panel = ctk.CTkLabel(self, text="")
        self.image_panel.pack(side="left", padx=10, pady=10, expand=True, fill="both")

        controls = ctk.CTkFrame(self, width=200)
        controls.pack(side="right", fill="y", padx=10)

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

        # self.brightness_slider = ctk.CTkSlider(controls, from_=0.1, to=2.0, command=self.update_image)
        # self.brightness_slider.set(1.0)
        # self.brightness_slider.pack(pady=5)

        # Sliders for adjustments
        self.brightness_slider = ctk.CTkSlider(controls, from_=-100, to=100, command=self.update_image)
        self.brightness_slider.set(0)
        self.brightness_slider.pack(pady=5)

        self.contrast_slider = ctk.CTkSlider(controls, from_=0.1, to=2.0, command=self.update_image)
        self.contrast_slider.set(1.0)
        self.contrast_slider.pack(pady=5)

        self.color_slider = ctk.CTkSlider(controls, from_=0.1, to=2.0, command=self.update_image)
        self.color_slider.set(1.0)
        self.color_slider.pack(pady=5)

        reset_btn = ctk.CTkButton(controls, text="Reset", command=self.reset_sliders)
        reset_btn.pack(pady=10)


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

    def update_image(self, _=None):
        if self.original_image is None:
            return
        threading.Thread(target=self.apply_adjustments).start()

    def apply_adjustments(self):
        img = self.original_image.copy()

        # Apply brightness & contrast efficiently using OpenCV
        brightness = self.brightness_slider.get()
        contrast = self.contrast_slider.get()
        img = cv2.convertScaleAbs(img, alpha=contrast, beta=brightness)

        self.display_image = img
        self.show_image(self.display_image)

    def show_image(self, img):
        # Resize for display to improve performance
        resized = cv2.resize(img, (600, 400))
        img_rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        tk_img = ImageTk.PhotoImage(pil_img)

        self.image_panel.configure(image=tk_img)
        self.image_panel.image = tk_img

    # Curve
    def draw_curve(self):
        self.canvas.delete("all")
        self.points = sorted(self.points)
        for x, y in self.points:
            self.canvas.create_oval(x-4, y-4, x+4, y+4, fill="white")
        for i in range(len(self.points) - 1):
            self.canvas.create_line(*self.points[i], *self.points[i+1], fill="cyan", width=2)
        
        lut = self.generate_lut()
        if self.display_image:
            self.apply_curve(lut)

    def apply_curve(self, lut):
        if self.original_image:
            img = self.original_image.copy().convert("RGB")
            r, g, b = img.split()
            r = r.point(lut.tolist())
            g = g.point(lut.tolist())
            b = b.point(lut.tolist())
            self.display_image = Image.merge("RGB", (r, g, b))
            self.show_image(self.display_image)

    def generate_lut(self):
        xs, ys = zip(*self.points)
        ys = [255 - y for y in ys]  # Invert y-values to match image brightness
        lut = np.interp(np.arange(256), xs, ys)
        lut = np.clip(lut, 0, 255).astype(np.uint8)
        return lut

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
    # End Curve

    def reset_sliders(self):
        self.brightness_slider.set(1.0)
        self.contrast_slider.set(1.0)
        self.color_slider.set(1.0)
        self.update_image()

if __name__ == "__main__":
    app = ImageEditorApp() 
    app.mainloop()