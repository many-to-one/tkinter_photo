import customtkinter as ctk
import tkinter as tk

import numpy as np

from app_widgets.accordion_section import create_accordion_section #AccordionSection

class RightSideBar(ctk.CTkFrame):
    def __init__(self, master, width):
        super().__init__(master, width=width)
        self.app = master
        self.grid_propagate(False)  # Prevent the frame from resizing to its content

        controls = ctk.CTkScrollableFrame(self, width=290, fg_color="#212121")
        controls.pack(fill="both", expand=True)

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
        white_balance_section = create_accordion_section(controls, "White Balance")
        self.temperature_slider = self.create_slider(white_balance_section, 1000, 10000, 6500, command=None, text="Temperature (K)", tipo='temperature')
        self.tint_slider = self.create_slider(white_balance_section, -150, 150, 0, command=None, text="Tint", tipo='tint')

        # Tone sliders inside tone_section
        tone_section = create_accordion_section(controls, "Tone")
        self.brightness_slider = self.create_slider(tone_section, -100, 100, 0, command=None, text="Brightness", tipo='brightness')
        self.contrast_slider = self.create_slider(tone_section, 0.1, 2.0, 1.0, command=None, text="Contrast", tipo='contrast')
        self.shadow_slider = self.create_slider(tone_section, 0.5, 2.0, 1.0, command=None, text="Shadows", tipo='shadows')
        self.light_slider = self.create_slider(tone_section, 0.5, 2.0, 1.0, command=None, text="Lights", tipo='lights')
        self.color_slider = self.create_slider(tone_section, 0.0, 2.0, 1.0, command=None, text="Saturation", tipo='saturation')
        self.dehaze_slider = self.create_slider(tone_section, -1.0, 1.0, 0.0, command=None, text="Dehaze", tipo='dehaze')
        self.fog_slider = self.create_slider(tone_section, -1.0, 1.0, 0.0, command=None, text="Fog", tipo='fog')

        # HSL
        self.hsl_section = create_accordion_section(controls, "HSL")

        self.hue_sliders = {}
        self.sat_sliders = {}
        self.lum_sliders = {}

        colors = ["Red", "Orange", "Yellow", "Green", "Aqua", "Blue", "Purple", "Magenta"]
        for color in colors:
            self.hue_sliders[color] = self.create_slider(
                self.hsl_section, -2.0, 2.0, 0,
                # self.hsl_section, 0.0, 1.0, 0,
                command=None,
                text=f"{color} Hue",
                tipo=f"hue_adj, {color}"
            )
            self.sat_sliders[color] = self.create_slider(
                self.hsl_section, 0.0, 2.0, 1,
                command=None,
                text=f"{color} Saturation",
                tipo=f"sat_adj, {color}"
            )
            self.lum_sliders[color] = self.create_slider(
                self.hsl_section, 0.0, 2.0, 1,
                command=None,
                text=f"{color} Luminance",
                tipo=f"lum_adj, {color}"
            )


        # Calibration Sliders
        self.calibration_section = create_accordion_section(controls, "Camera Calibration")

        self.shadow_hue_sliders = {}
        self.shadow_sat_sliders = {}
        self.primary_hue_sliders = {}
        self.primary_sat_sliders = {}

        # Shadows Tint
        self.shadows_tint = self.create_slider(self.calibration_section, -1.0, 1.0, 0.0, command=None, text="Shadows/tint", tipo='shadows_tint')

        # Shadows: Red, Green, Blue
        shadow_colors = ["Red", "Green", "Blue"]

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




    def create_slider(self, parent, from_, to, default, command, text, tipo, gradient=False):

        frame = ctk.CTkFrame(parent)  # Optional: wrap each slider in a frame
        frame.pack(fill="x", pady=4)

        label = ctk.CTkLabel(frame, text=text)
        label.pack(anchor="w")

        print(f' ----------- create_slider TIPO------------- ', tipo)
        slider = ctk.CTkSlider(frame, from_=from_, to=to, command=lambda value: self.on_slider_change(value, tipo, gradient))
        slider.set(default)
        print(f' ----------- slider {text} ------------- ', slider.get())
        slider.pack(fill="x")
        slider.bind("<ButtonRelease-1>", self.on_slider_release)  # <- trigger on release

        return slider

    def on_slider_change(self, value, tipo, gradient=False):

        global __gradient
        __gradient = gradient
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
        print(" ######################## __gradient: ######################## ", __gradient)

        # if __gradient == True:
        #     self.update_gradient_changes(slider_tipo, current_slider_value)
        # else:
        #     self.apply_adjustments(slider_tipo, current_slider_value)
        self.app.refresh_image()

    
    # Curve
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

    def draw_curve(self):
        self.canvas.delete("all")
        self.points = sorted(self.points)
        for x, y in self.points:
            self.canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill="white")
        for i in range(len(self.points) - 1):
            self.canvas.create_line(*self.points[i], *self.points[i + 1], fill="cyan", width=2)

        # Only apply curve now (fast update)
        if self.app.display_image is not None:
            self.app.apply_curve_only()
            # threading.Thread(target=self.apply_adjustments).start()