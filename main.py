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
import colorsys

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

from adjustments_c.brightness_c import apply_all_adjustments_c

from apply_section.apply_adjustments import apply_adjustments
from apply_section.apply_adjustments_high_res import apply_adjustments_high_res


from info_windows.window_process import InfoWindow
from info_windows.init_window import InitWindow
from zoom.zoom import Zoom

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
        self.curve_base_image = None
        self.display_image = None
        self.high_res_result = None

        # Zoom logic
        self.zoom_level = 1.0  # Default 100%
        self.zoom_step = 0.1   # 10% per step

        # Zoom with buttons
        self.root.bind('<Control-minus>', self.zoom_out)
        self.root.bind('<Control-plus>', self.zoom_in)
        self.root.bind('<Control-equal>', self.zoom_in)  # Handle Ctrl + = (some keyboards)


        self.executor = ThreadPoolExecutor(max_workers=1)

        # UI Setup
        self.setup_ui()
        # self.start_warmup()
        # self.start_init_window(self.run_warmup_and_close_info, "Initializing...")
        # self.start_init("Initializing...")


# ---------------------------------------------------------------------------------- #
# Info window and process                                                           #
# ---------------------------------------------------------------------------------- #

    def start_process(self, target, text):
        """Start a process and display the info window while running."""
        self.info_window = InfoWindow(self, text)  # Open InfoWindow
        threading.Thread(target=self.run_process, args=(target,), daemon=True).start()

    def run_process(self, target):
        """Execute the function and close the info window when done."""
        target()  # Run the function
        self.info_window.destroy()

# ---------------------------------------------------------------------------------- #
# End of info window and proccess                                                    #
# ---------------------------------------------------------------------------------- #

# ---------------------------------------------------------------------------------- #
# Init proccess with info window                                                     #
# ---------------------------------------------------------------------------------- #

    def start_init(self, text):
        """Start a process and display the info window while running."""
        self.info_window = InitWindow(self, text)  # Open InfoWindow
        
        
# ---------------------------------------------------------------------------------- #
# End of Init proccess with info window                                              #
# ---------------------------------------------------------------------------------- #

# ---------------------------------------------------------------------------------- #
# Zoom logic                                                                         #
# ---------------------------------------------------------------------------------- #

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


# ---------------------------------------------------------------------------------- #
# Enf of Zoom logic                                                                  #
# ---------------------------------------------------------------------------------- #


    def setup_ui(self): 

        self.image_panel = ctk.CTkLabel(self, text="", bg_color="#333333")
        self.image_panel.pack(side="left", expand=True, fill="both")

        # Zoom with the mouse wheel
        self.image_panel.bind("<MouseWheel>", self.on_mousewheel)  # Windows
        self.image_panel.bind("<Button-4>", self.on_mousewheel)    # Linux
        self.image_panel.bind("<Button-5>", self.on_mousewheel)

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


        # White balance accordion section
        white_balance_section = self.create_accordion_section(controls, "White Balance")
        self.temperature_slider = self.create_slider(white_balance_section, 1000, 10000, 6500, command=None, text="Temperature (K)", tipo='temperature')
        self.tint_slider = self.create_slider(white_balance_section, -150, 150, 0, command=None, text="Tint", tipo='tint')

        # Tone sliders inside tone_section
        tone_section = self.create_accordion_section(controls, "Tone")
        self.brightness_slider = self.create_slider(tone_section, -100, 100, 0, command=None, text="Brightness", tipo='brightness')
        self.contrast_slider = self.create_slider(tone_section, 0.1, 2.0, 1.0, command=None, text="Contrast", tipo='contrast')
        self.shadow_slider = self.create_slider(tone_section, 0.5, 2.0, 1.0, command=None, text="Shadows", tipo='shadows')
        self.light_slider = self.create_slider(tone_section, 0.5, 2.0, 1.0, command=None, text="Lights", tipo='lights')
        self.color_slider = self.create_slider(tone_section, 0.0, 2.0, 1.0, command=None, text="Saturation", tipo='saturation')
        self.dehaze_slider = self.create_slider(tone_section, -2.0, 2.0, 0.0, command=None, text="Dehaze", tipo='dehaze')
        self.fog_slider = self.create_slider(tone_section, -2.0, 2.0, 0.0, command=None, text="Fog", tipo='fog')


        # HSL
        self.hsl_section = self.create_accordion_section(controls, "HSL")

        self.hue_sliders = {}
        self.sat_sliders = {}
        self.lum_sliders = {}

        colors = ["Red", "Orange", "Yellow", "Green", "Aqua", "Blue", "Purple", "Magenta"]
        for color in colors:
            self.hue_sliders[color] = self.create_slider(
                self.hsl_section, -180, 180, 0,
                command=None,
                text=f"{color} Hue",
                tipo=f"hue_adj, {color}"
            )
            self.sat_sliders[color] = self.create_slider(
                self.hsl_section, -180, 180, 0,
                command=None,
                text=f"{color} Saturation",
                tipo=f"sat_adj, {color}"
            )
            self.lum_sliders[color] = self.create_slider(
                self.hsl_section, -180, 180, 0,
                command=None,
                text=f"{color} Luminance",
                tipo=f"lum_adj, {color}"
            )


        # Calibration Sliders
        self.calibration_section = self.create_accordion_section(controls, "Camera Calibration")

        self.shadow_hue_sliders = {}
        self.shadow_sat_sliders = {}
        self.primary_hue_sliders = {}
        self.primary_sat_sliders = {}

        # Shadows: Red, Green, Blue
        shadow_colors = ["Red", "Green", "Blue"]
        for color in shadow_colors:
            self.shadow_hue_sliders[color] = self.create_slider(
                self.calibration_section, -1.0, 1.0, 0.0,
                command=None,
                text=f"Shadows {color} Hue",
                tipo=f"shadows_hue_adj, {color}"
            )
            self.shadow_sat_sliders[color] = self.create_slider(
                self.calibration_section, 0.0, 2.0, 1.0,
                # self.calibration_section, -180, 180, 1.0,
                command=None,
                text=f"Shadows {color} Saturation",
                tipo=f"shadows_sat_adj, {color}"
            )

        # RGB Primaries: Red, Green, Blue
        for color in shadow_colors:  # same as RGB
            self.primary_hue_sliders[color] = self.create_slider(
                self.calibration_section, -1.0, 1.0, 0.0,
                # self.calibration_section, -180, 180, 1.0,
                command=None,
                text=f"{color} Primary Hue",
                tipo=f"primary_hue_adj, {color}"
            )
            self.primary_sat_sliders[color] = self.create_slider(
                self.calibration_section, 0.0, 2.0, 1.0,
                # self.calibration_section, -180, 180, 1.0,
                command=None,
                text=f"{color} Primary Saturation",
                tipo=f"primary_sat_adj, {color}"
            )




        reset_btn = ctk.CTkButton(controls, text="Reset", command=self.reset_sliders)
        reset_btn.pack(pady=10)

        save_image_btn = ctk.CTkButton(controls, text="Save as...", command=lambda: self.start_process(self.save_high_res_image_pil, "Saving..."))
        save_image_btn.pack(pady=10)
    



    def toggle_section(self, frame):
        if frame.winfo_viewable():
            frame.pack_forget()
        else:
            frame.pack(fill="x", padx=10, pady=5)


    def create_slider(self, parent, from_, to, default, command, text, tipo):

        frame = ctk.CTkFrame(parent)  # Optional: wrap each slider in a frame
        frame.pack(fill="x", pady=4)

        label = ctk.CTkLabel(frame, text=text)
        label.pack(anchor="w")

        print(f' ----------- create_slider TIPO------------- ', tipo)
        slider = ctk.CTkSlider(frame, from_=from_, to=to, command=lambda value: self.on_slider_change(value, tipo))
        slider.set(default)
        print(f' ----------- slider {text} ------------- ', slider.get())
        slider.pack(fill="x")
        slider.bind("<ButtonRelease-1>", self.on_slider_release)  # <- trigger on release

        return slider

    def on_slider_change(self, value, tipo):
        # This runs every time the slider is dragged (live preview optional)
        global current_slider_value
        # global slider_command
        global slider_tipo
        current_slider_value = value  # just store value
        # slider_command = command
        slider_tipo = tipo

    def on_slider_release(self, event):
        # Called only when user releases the slider
        print(" ######################## Released at: ######################## ", current_slider_value)
        print(" ######################## on_slider_release: ######################## ", slider_tipo)
        self.apply_adjustments(slider_tipo, current_slider_value)

    def update_image(self, value, tipo, _=None):
        print(" ------------------ update_image tipo ------------------ ", tipo)
        print(" ------------------ update_image value ------------------ ", value)
        if self.original_image is None:
            return
        # self.executor.submit(self.apply_adjustments, tipo) 
        self.executor.submit(self.on_slider_change, value, tipo) 


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
        
        elif path.lower().endswith(".tiff"):
            pil_img = Image.open(path)
            self.original_image = np.array(pil_img)
        
        else:
            self.original_image = cv2.imread(path, cv2.IMREAD_UNCHANGED)

        if self.original_image is None:
            print("Error loading image!")
            return

        # Create small version for fast processing
        max_dim = 2000
        height, width = self.original_image.shape[:2]
        scale = min(max_dim / width, max_dim / height, 1.0)
        new_size = (int(width * scale), int(height * scale))
        self.small_image = cv2.resize(self.original_image, new_size, interpolation=cv2.INTER_AREA)

        self.display_image = self.small_image.copy()  # Use small image for display
        self.show_image(self.display_image)



    def apply_adjustments(self, tipo, value, high_res=False):

        img = self.small_image.copy()

        # Tone
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

        hue_adj = {color: slider.get() for color, slider in self.hue_sliders.items()}
        sat_adj = {color: slider.get() for color, slider in self.sat_sliders.items()}
        lum_adj = {color: slider.get() for color, slider in self.lum_sliders.items()}

        img = apply_all_adjustments_c(
            img,
            brightness, contrast, saturation,
            shadow_factor, light_factor,
            temperature, tint,
            [hue_adj[color] for color in ["Red", "Orange", "Yellow", "Green", "Aqua", "Blue"]],
            [sat_adj[color] for color in ["Red", "Orange", "Yellow", "Green", "Aqua", "Blue"]],
            [lum_adj[color] for color in ["Red", "Orange", "Yellow", "Green", "Aqua", "Blue"]],
        )


        self.display_image = img
        self.show_image(self.display_image)



    # def apply_adjustments(self, tipo, value, high_res=False):

    #     print('----------- tipo ------------', tipo)
    #     print('----------- value ///// ------------', value)
    #     img = self.small_image.copy()

    #     # Tone
    #     brightness = self.brightness_slider.get()
    #     contrast = self.contrast_slider.get()
    #     shadow_factor = self.shadow_slider.get()
    #     light_factor = self.light_slider.get()
    #     saturation = self.color_slider.get()
    #     dehaze = self.dehaze_slider.get()
    #     fog = self.fog_slider.get()

    #     # White balance
    #     temperature = int(self.temperature_slider.get())
    #     tint = int(self.tint_slider.get())

    #     img = apply_kelvin_temperature(img, temperature)
    #     img = apply_tint_shift(img, tint)

    #     # img = apply_brightness(img, brightness)
    #     img = apply_brightness_c(img, brightness)
    #     img = apply_contrast(img, contrast)
    #     img = adjust_saturation_rgb(img, saturation)
    #     img = adjust_shadows_lights(img, shadow_factor, light_factor)
    #     img = dehaze_effect(img, dehaze)
    #     img = fog_effect(img, fog)

    #     hue_adj = {color: slider.get() for color, slider in self.hue_sliders.items()}
    #     sat_adj = {color: slider.get() for color, slider in self.sat_sliders.items()}
    #     lum_adj = {color: slider.get() for color, slider in self.lum_sliders.items()}

    #     print(' ----------- hue_adj ------------ ', hue_adj)
    #     print(' ----------- sat_adj ------------ ', sat_adj)
    #     print(' ----------- lum_adj ------------ ', lum_adj)

    #     img = apply_hsl_superfast(img, hue_adj, sat_adj, lum_adj)   

    #     primary_hue = {
    #         "Red": self.primary_hue_sliders["Red"].get(),
    #         "Green": self.primary_hue_sliders["Green"].get(),
    #         "Blue": self.primary_hue_sliders["Blue"].get(),
    #     }
    #     primary_sat = {
    #         "Red": self.primary_sat_sliders["Red"].get(),
    #         "Green": self.primary_sat_sliders["Green"].get(),
    #         "Blue": self.primary_sat_sliders["Blue"].get(),
    #     }

    #     print(' ----------- primary_hue ------------ ', primary_hue)
    #     print(' ----------- primary_sat ------------ ', primary_sat)

    #     img = apply_primary_calibration_rgb(
    #         img,
    #         primary_hue["Red"], primary_hue["Green"], primary_hue["Blue"],
    #         primary_sat["Red"], primary_sat["Green"], primary_sat["Blue"]
    #     )

    #     shadow_hue = {
    #         color: self.shadow_hue_sliders[color].get() for color in ["Red", "Green", "Blue"]
    #     }
    #     shadow_sat = {
    #         color: self.shadow_sat_sliders[color].get() for color in ["Red", "Green", "Blue"]
    #     }

    #     img = apply_shadow_calibration_rgb(
    #         img,
    #         shadow_hue['Red'], shadow_hue['Green'], shadow_hue['Blue'],
    #         shadow_sat['Red'], shadow_sat['Green'], shadow_sat['Blue']
    #     )


    #     # # Eyedropper
    #     # if hasattr(self, 'eyedropper_pixel') and self.eyedropper_pixel is not None:
    #     #     img = apply_white_balance_eyedropper(img, self.eyedropper_pixel)


    #     # Curve
    #     self.curve_base_image = img.copy()

    #     lut = self.generate_lut()

    #     b, g, r = cv2.split(img)
    #     r = cv2.LUT(r, lut)
    #     g = cv2.LUT(g, lut)
    #     b = cv2.LUT(b, lut)
    #     img = cv2.merge((b, g, r))


    #     self.display_image = img
    #     self.show_image(self.display_image)




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
        tk_img = ImageTk.PhotoImage(pil_img)

        self.image_panel.configure(image=tk_img)
        self.image_panel.image = tk_img




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

        lut = self.generate_lut()

        b, g, r = cv2.split(img)
        r = cv2.LUT(r, lut)
        g = cv2.LUT(g, lut)
        b = cv2.LUT(b, lut)
        img = cv2.merge((b, g, r))
        # self.cached_image['img'] = img

        self.display_image = img
        self.show_image(self.display_image)

        # thread = threading.Thread(target=self.apply_adjustments_high_res)
        # thread.start()

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

    
    # from PIL import Image

    def save_high_res_image_pil(self):
        
        try:
            res = apply_adjustments_high_res(
                self.original_image.copy(),
                
                # Tone
                self.brightness_slider.get(),
                self.contrast_slider.get(),
                self.shadow_slider.get(),
                self.light_slider.get(),
                self.color_slider.get(),
                self.dehaze_slider.get(),
                self.fog_slider.get(),

                # White balance
                int(self.temperature_slider.get()),
                int(self.tint_slider.get()),

                self.hue_sliders,
                self.sat_sliders,
                self.lum_sliders,

                self.shadow_hue_sliders,
                self.shadow_sat_sliders,
                self.primary_hue_sliders,
                self.primary_sat_sliders,

                self.generate_lut()

            )

            if res is None:
                # self.close_info_window()
                raise ValueError("High-res image processing returned None.")


            file_path = filedialog.asksaveasfilename(
                defaultextension=".jpg",
                filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png"), ("TIFF", "*.tiff"), ("All Files", "*.*")]
            )

            if not file_path:
                print("Save cancelled.")
                # self.close_info_window()
                return

            img_bgr = np.clip(res, 0, 255).astype(np.uint8)
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)
            pil_img.save(file_path)
            print(f"Image saved to {file_path}")

        except Exception as e:
            # self.close_info_window()
            print("Failed to save image:", str(e))

        # finally:
            # self.close_info_window()


if __name__ == "__main__":
    app = ImageEditorApp()
    app.mainloop()
