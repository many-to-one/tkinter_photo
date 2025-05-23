import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import cv2
import numpy as np
from PIL import Image, ImageTk
import threading
import rawpy

class ImageEditorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Photo Editor - Tkinter Lightroom")
        self.geometry("1000x600")

        # Image variables
        self.original_image = None
        self.display_image = None

        # UI Setup
        self.setup_ui()

    def setup_ui(self):
        self.image_panel = ctk.CTkLabel(self, text="")
        self.image_panel.pack(side="left", padx=10, pady=10, expand=True, fill="both")

        controls = ctk.CTkFrame(self, width=200)
        controls.pack(side="right", fill="y", padx=10)

        open_btn = ctk.CTkButton(controls, text="Open Image", command=self.open_image)
        open_btn.pack(pady=10)

        # Sliders for adjustments
        self.brightness_slider = ctk.CTkSlider(controls, from_=-100, to=100, command=self.update_image)
        self.brightness_slider.set(0)
        self.brightness_slider.pack(pady=5)

        self.contrast_slider = ctk.CTkSlider(controls, from_=0.5, to=3.0, command=self.update_image)
        self.contrast_slider.set(1.0)
        self.contrast_slider.pack(pady=5)

        reset_btn = ctk.CTkButton(controls, text="Reset", command=self.reset_sliders)
        reset_btn.pack(pady=10)

    # def open_image(self):
    #     path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.png *.jpeg *.cr2 ")])
    #     if path:
    #         self.original_image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    #         if self.original_image is None:
    #             print("Error loading image!")
    #             return
    #         self.display_image = self.original_image.copy()
    #         self.show_image(self.display_image)

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

    # def show_image(self, img):
    #     resized = img.resize((600, 400))
    #     tk_img = ImageTk.PhotoImage(resized)
    #     self.image_panel.configure(image=tk_img)
    #     self.image_panel.image = tk_img

    def reset_sliders(self):
        self.brightness_slider.set(0)
        self.contrast_slider.set(1.0)
        self.update_image()

if __name__ == "__main__":
    app = ImageEditorApp()
    app.mainloop()
