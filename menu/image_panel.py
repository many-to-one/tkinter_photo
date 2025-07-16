import customtkinter as ctk
from customtkinter import CTkImage
import tkinter as tk
from PIL import Image, ImageTk
import cv2


class ImagePanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        self.app = master
        self.configure(fg_color="#1e1e1e")  # dark background

        # Label to show the image
        self.image_label = ctk.CTkLabel(self, text="")
        self.image_label.pack(expand=True, fill="both")  # or use .grid() if needed

        self.tk_image = None  # Keep a reference to avoid GC

        # Zoom logic
        self.zoom_level = 1.0  # Default 100%
        self.zoom_step = 0.1   # 10% per step

    
    def zoom_in(self, event=None):
        self.zoom_level = min(self.zoom_level + self.zoom_step, 10.0)
        self.show_image(self.display_image)

    def zoom_out(self, event=None):
        self.zoom_level = max(self.zoom_level - self.zoom_step, 0.1)
        self.show_image(self.display_image)

    def on_mousewheel(self, event):
        if hasattr(event, 'delta'):
            if event.delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        elif event.num == 4:
            self.zoom_in()
        elif event.num == 5:
            self.zoom_out()


    def update_image(self, value, tipo, _=None):
        print(" ------------------ update_image tipo ------------------ ", tipo)
        print(" ------------------ update_image value ------------------ ", value)
        if self.app.original_image is None:
            return
        # self.executor.submit(self.apply_adjustments, tipo) 
        self.executor.submit(self.app.right_menu.on_slider_change, value, tipo) 

    def show_image(self, img):

        if not hasattr(self, "zoom_level"):
            self.zoom_level = 1.0

        h, w = img.shape[:2]
        zoom = self.zoom_level

        # Calculate the zoomed dimensions
        zoom_w = int(w / zoom)
        zoom_h = int(h / zoom)

        # Center crop coordinates
        center_x, center_y = w // 2, h // 2
        x1 = max(center_x - zoom_w // 2, 0)
        y1 = max(center_y - zoom_h // 2, 0)
        x2 = min(x1 + zoom_w, w)
        y2 = min(y1 + zoom_h, h)

        # Crop and resize back to 800x600
        cropped = img[y1:y2, x1:x2]

        display_width = 1000
        h, w = cropped.shape[:2]
        aspect_ratio = h / w
        display_height = int(display_width * aspect_ratio)
        display_size = (display_width, display_height)

        resized = cv2.resize(cropped, display_size, interpolation=cv2.INTER_LINEAR)

        img_rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)

        self.tk_img = CTkImage(light_image=pil_img, size=display_size)
        self.app.image_label.configure(image=self.tk_img, text="")  # clear text too

