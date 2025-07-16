import customtkinter as ctk
from tkinter import filedialog
import cv2
import rawpy
# import numpy as np
from PIL import Image, ImageTk, ImageEnhance, ImageDraw
# import math

from .image_panel import ImagePanel

class TopMenu(ctk.CTkFrame):
    def __init__(self, master, height):
        super().__init__(master, height=height)
        self.app = master
        self.image_panel = ImagePanel(master)
        self.grid_propagate(False)

        # Define buttons and their commands
        buttons = [
            ("Open Image", self.open_image),
            ("Save", self.save_image),
            ("Reset", self.reset_image)
        ]

        # Create buttons
        for i, (label, cmd) in enumerate(buttons):
            btn = ctk.CTkButton(self, text=label, width=20, fg_color="#333333", command=cmd)
            btn.grid(row=0, column=i, padx=5, pady=2, sticky="w")


    def open_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.png *.jpeg *.tiff *.cr2")])
        
        if path.lower().endswith(".cr2"):  # RAW format handling
            raw = rawpy.imread(path)
            rgb = raw.postprocess()
            self.app.original_image = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        
        elif path.lower().endswith(".tiff"):
            pil_img = Image.open(path)
            self.app.original_image = np.array(pil_img)
        
        else:
            self.app.original_image = cv2.imread(path, cv2.IMREAD_UNCHANGED)

        if self.app.original_image is None:
            print("Error loading image!")
            return

        # Create small version for fast processing
        max_dim = 2000
        height, width = self.app.original_image.shape[:2]
        scale = min(max_dim / width, max_dim / height, 1.0)
        new_size = (int(width * scale), int(height * scale))
        self.app.small_image = cv2.resize(self.app.original_image, new_size, interpolation=cv2.INTER_AREA)

        self.app.display_image = self.app.small_image.copy()  # Use small image for display
        self.image_panel.show_image(self.app.display_image)

    def save_image(self):
        print("Save clicked")

    def reset_image(self):
        print("Reset clicked")