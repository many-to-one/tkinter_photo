import cv2
import numpy as np
import math


class GradientController:
    def __init__(self, app):
        self.app = app
        self.drag_mode = None
        self.last_mouse_y = None
        self.selected_index = None
        self.selected_gradient_index = None
        self.rotating_gradient = None


    def draw_gradient_edges(self, img, gradients):
        for g in gradients:
            if not g.get("active"):
                continue

            x0, y0 = g["start"]
            x1, y1 = g["end"]
            angle = g.get("angle", 0.0)

            # Compute center and length/width
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            length = math.hypot(x1 - x0, y1 - y0)
            width = g.get("width", 200)  # fixed width for visual area

            rad = math.radians(angle)
            cos_a = math.cos(rad)
            sin_a = math.sin(rad)

            # Calculate the 4 corners of the rotated rectangle
            dx = (length / 2) * cos_a
            dy = (length / 2) * sin_a
            wx = (width / 2) * sin_a
            wy = (width / 2) * cos_a

            p1 = (int(cx - dx - wx), int(cy - dy + wy))
            p2 = (int(cx + dx - wx), int(cy + dy + wy))
            p3 = (int(cx + dx + wx), int(cy + dy - wy))
            p4 = (int(cx - dx + wx), int(cy - dy - wy))

            pts = np.array([p1, p2, p3, p4], dtype=np.int32).reshape((-1, 1, 2))

            # Draw the polygon
            cv2.polylines(img, [pts], isClosed=True, color=(0, 255, 0), thickness=2)

        return img


    def on_mouse_down(self, event):
        x, y = event.x * 2, event.y * 2  # scale to match small_image size
        clicked_x, clicked_y = event.x, event.y

        for i, g in enumerate(self.app.gradients):
            x0, y0 = g["start"]
            x1, y1 = g["end"]

            x0, x1 = sorted([x0, x1])
            y0, y1 = sorted([y0, y1])

            hx, hy = g["handle"]

            # Check if near top line
            if abs(y - y0) < 10 and x0 <= x <= x1:
                self.drag_mode = "resize_top"
                self.selected_gradient_index = i
                break
            # Near bottom line
            elif abs(y - y1) < 10 and x0 <= x <= x1:
                self.drag_mode = "resize_bottom"
                self.selected_gradient_index = i
                break
            # Inside box = move
            elif y0 < y < y1 and x0 <= x <= x1:
                self.drag_mode = "move"
                self.selected_gradient_index = i
                self.last_mouse_y = y
                break
            # rotation
            elif abs(x - hx) < 20 and abs(y - hy) < 20:
                print(' ------------- rotate + ------------- ')
                self.drag_mode = "rotate"
                self.selected_gradient_index = i
                break
        
            print(' ------------- rotate x - hx ------------- ', abs(x - hx))
            print(' ------------- rotate y - hy ------------- ', abs(y - hy))
        print(' ------------- self.drag_mode ------------- ', self.drag_mode)


    def on_mouse_drag(self, event):
        if self.selected_gradient_index is None:
            return

        x, y = event.x * 2, event.y * 2
        g = self.app.gradients[self.selected_gradient_index]

        x0, y0 = g["start"]
        x1, y1 = g["end"]
        x0, x1 = sorted([x0, x1])
        y0, y1 = sorted([y0, y1])

        if self.drag_mode == "resize_top":
            self.app.gradients[self.selected_gradient_index]["start"] = (x0, y)
        elif self.drag_mode == "resize_bottom":
            self.app.gradients[self.selected_gradient_index]["end"] = (x1, y)
        elif self.drag_mode == "move":
            dy = y - self.last_mouse_y
            self.app.gradients[self.selected_gradient_index]["start"] = (x0, y0 + dy)
            self.app.gradients[self.selected_gradient_index]["end"] = (x1, y1 + dy)
            self.last_mouse_y = y
        elif self.drag_mode == "rotate":
            print(' ------------- rotate ------------- ')
            dy = y - self.last_mouse_y
            new_start = (x0, y0 + dy)
            new_end = (x1, y1 + dy)
            self.app.gradients[self.selected_gradient_index]["start"] = new_start
            self.app.gradients[self.selected_gradient_index]["end"] = new_end
            self.last_mouse_y = y

            # Recalculate handle position
            cx = (new_start[0] + new_end[0]) // 2
            cy = (new_start[1] + new_end[1]) // 2
            angle = self.app.gradients[self.selected_gradient_index]["angle"]
            self.app.gradients[self.selected_gradient_index]["handle"] = self.calculate_rotation_handle(cx, cy, angle)

            # self.app.refresh_image()


        print(' ------------- on_mouse_drag ------------- ', self.drag_mode)
        # self.apply_gradients(self.app.small_image.copy(), self.app.gradients)
        self.app.refresh_image()

    def on_mouse_up(self, event):
        self.drag_mode = None
        self.selected_gradient_index = None
        # self.rotating_gradient = None

    
    def on_mouse_move(self, event):

        x, y = event.x * 2, event.y * 2
        for g in self.app.gradients:
            hx, hy = g["handle"]
            if abs(x - hx) < 20 and abs(y - hy) < 20:
                self.app.config(cursor="exchange")  # or "circle", or a custom cursor
                self.drag_mode = "rotate"
                print(' --------------------- on_mouse_move - rotate - hx, hy --------------------- ', hx, hy)
                return

        self.app.config(cursor="arrow")


    def on_mouse_double_click(self, event):

        x, y = event.x * 2, event.y * 2

        found = False

        for g in self.app.gradients:
            g["active"] = False  # deactivate all by default
            if self.is_inside_gradient(x, y, g):
                self.rotating_gradient = g
                g["active"] = True
                found = True
                self.app.slider_frame.pack(fill='x', padx=10, pady=10)  # Show
                self.load_gradient_to_sliders(g)  # <-- Load values
                break

        if not found:
            self.app.slider_frame.pack_forget()
            self.app.panel.width = 0

        print(' --------------------- on_mouse_double_click --------------------- ')


    def is_inside_gradient(self, x, y, gradient):
        print(' ------------- is_inside_gradient x, y ------------- ', x, y)
        x0, y0 = gradient["start"]
        x1, y1 = gradient["end"]

        x_min, x_max = sorted([x0, x1])
        y_min, y_max = sorted([y0, y1])

        print(' ------------- is_inside_gradient x_min, x_max ------------- ', x_min, x_max)
        print(' ------------- is_inside_gradient y_min, y_max ------------- ', y_min, y_max)

        return x_min <= x <= x_max and y_min <= y <= y_max

    
    def load_gradient_to_sliders(self, gradient):
        for name in ['brightness', 'contrast', 'temperature', 'tint', 'strength']:
            if name in self.app.sliders and name in gradient:
                slider, var = self.app.sliders[name]
                var.set(gradient[name])


    def clear_sliders(self):
        for name, (slider, var) in self.app.sliders.items():
            var.set(0.0 if name != 'strength' else 1.0)


    def calculate_rotation_handle(self, cx, cy, angle_deg, offset=50):
        # print(' --------------------- calculate_rotation_handle --------------------- ', cx, cy, angle_deg)
        angle_rad = math.radians(angle_deg)
        hx = int(cx + offset * math.cos(angle_rad - math.pi / 2))  # above center
        hy = int(cy + offset * math.sin(angle_rad - math.pi / 2))
        print(' --------------------- calculate_rotation_handle --------------------- ', hx, hy)
        return (hx, hy)


    def update_gradient_rotation(self, gradient):
        angle = gradient["angle"] = gradient.get("rotate")  # Degrees
        print(' --------------------- update_gradient_rotation ***angle --------------------- ', angle)
        cx = (gradient["start"][0] + gradient["end"][0]) / 2
        cy = (gradient["start"][1] + gradient["end"][1]) / 2

        length = math.dist(gradient["start"], gradient["end"]) / 2
        radians = math.radians(angle)

        dx = length * math.cos(radians)
        dy = length * math.sin(radians)

        gradient["start"] = (int(cx - dx), int(cy - dy))
        gradient["end"]   = (int(cx + dx), int(cy + dy))

        # Recalculate handle position too if needed
        gradient["handle"] = self.calculate_rotation_handle(cx, cy, angle)



    def delete_gradient(self, event):

        confirm = InfoWindow(self, 'Delete ?')
        answer = confirm.get_answer()
        print(' --------------------- answer --------------------- ', answer)

        if answer == False:
            return
        else:
            x, y = event.x * 2, event.y * 2

            for i, g in enumerate(self.app.gradients):
                x0, y0 = g["start"]
                x1, y1 = g["end"]

                x0, x1 = sorted([x0, x1])
                y0, y1 = sorted([y0, y1])

                print(' --------------------- delete_gradient x, y --------------------- ', x, y, i)
                print(' --------------------- delete_gradient x0, y0 --------------------- ', x0, y0)
                print(' --------------------- delete_gradient x1, y1 --------------------- ', x1, y1)

                if x0 <= x <= x1 and y0 <= y <= y1:
                    del [i]
                    self.apply_gradients(self.app.small_image.copy(), self.app.gradients)
                    break


    # def apply_gradients(self, img, gradients):
    #     img = img.astype(np.float32) / 255.0  # Normalize image

    #     for g in gradients:
    #         if not g["start"] or not g["end"]:
    #             continue

    #         x0, y0 = g["start"]
    #         x1, y1 = g["end"]
    #         x0, x1 = sorted([int(x0), int(x1)])
    #         y0, y1 = sorted([int(y0), int(y1)])
    #         w, h = x1 - x0, y1 - y0

    #         if w <= 0 or h <= 0:
    #             continue

    #         # Extract adjustments
    #         temperature = g.get("temperature", 0.0)
    #         tint = g.get("tint", 0.0)
    #         brightness = g.get("brightness", 0.0)
    #         contrast = g.get("contrast", 0.0)
    #         angle = g.get("angle", 45)  # default angle = 90° (vertical)

    #         # Generate fade mask with rotation
    #         fade = self.generate_rotated_fade_mask(w, h, angle).reshape(h, w, 1)

    #         # Extract region
    #         region = img[y0:y1, x0:x1]

    #         # Skip invalid region
    #         if region.shape[:2] != fade.shape[:2]:
    #             continue

    #         # --- Apply adjustments with fade ---

    #         # Temperature (cool to warm: blue ↔ red)
    #         temp_strength = 0.6
    #         region[:, :, 0] += (-temperature * temp_strength) * fade[:, :, 0]  # Blue
    #         region[:, :, 2] += (temperature * temp_strength) * fade[:, :, 0]   # Red

    #         # Tint (green ↔ magenta)
    #         tint_strength = 0.6
    #         region[:, :, 1] += (tint * tint_strength) * fade[:, :, 0]         # Green
    #         region[:, :, 0] += (-tint * tint_strength * 0.5) * fade[:, :, 0]  # Blue
    #         region[:, :, 2] += (-tint * tint_strength * 0.5) * fade[:, :, 0]  # Red

    #         # Brightness
    #         region += brightness * fade

    #         # Contrast
    #         mean = 0.5
    #         region = (region - mean) * (1 + contrast * fade) + mean

    #         # Clip and paste back
    #         img[y0:y1, x0:x1] = np.clip(region, 0, 1)

    #     return (img * 255).astype(np.uint8)

# ***************************************************************************


    def generate_rotated_fade_mask(self, width, height, angle):
        fade = np.tile(np.linspace(1.0, 0.0, height)[:, np.newaxis], (1, width))

        # Obrót z PIL (łatwo)
        import cv2
        center = (width // 2, height // 2)
        rot_mat = cv2.getRotationMatrix2D(center, -angle, 1.0)
        rotated = cv2.warpAffine(fade.astype(np.float32), rot_mat, (width, height), flags=cv2.INTER_LINEAR)

        return np.clip(rotated, 0, 1)



    def apply_gradients(self, img, gradients):
        img = img.astype(np.float32) / 255.0  # Normalize
        img_h, img_w = img.shape[:2]

        for g in gradients:
            if not g["start"] or not g["end"]:
                continue

            # Get coordinates
            x0, y0 = g["start"]
            x1, y1 = g["end"]

            x0, x1 = sorted([int(x0), int(x1)])
            y0, y1 = sorted([int(y0), int(y1)])

            x0 = max(0, min(x0, img_w))
            x1 = max(0, min(x1, img_w))
            y0 = max(0, min(y0, img_h))
            y1 = max(0, min(y1, img_h))

            w, h = x1 - x0, y1 - y0
            if w <= 0 or h <= 0:
                continue

            angle = g.get("angle", 0.0)

            # Crop region from image
            region = img[y0:y1, x0:x1]
            if region.size == 0:
                continue

            # Generate rotated fade mask matching region size
            fade = self.generate_rotated_fade_mask(w, h, angle).reshape(h, w, 1)

            # Extract parameters
            temperature = g.get("temperature", 0)
            tint = g.get("tint", 0)
            brightness = g.get("brightness", 0)
            contrast = g.get("contrast", 0)

            # Copy region to modify
            region = region.copy()

            # --- White balance ---
            temp_strength = 0.6
            tint_strength = 0.6

            region[:, :, 0] += (-temperature * temp_strength) * fade[:, :, 0]  # Blue
            region[:, :, 2] += (temperature * temp_strength) * fade[:, :, 0]   # Red

            region[:, :, 1] += (tint * tint_strength) * fade[:, :, 0]          # Green
            region[:, :, 0] += (-tint * tint_strength * 0.5) * fade[:, :, 0]   # Blue (magenta)
            region[:, :, 2] += (-tint * tint_strength * 0.5) * fade[:, :, 0]   # Red (magenta)

            # Brightness
            region += brightness * fade

            # Contrast
            mean = 0.5
            region = (region - mean) * (1 + contrast * fade) + mean

            # Write back
            img[y0:y1, x0:x1] = np.clip(region, 0, 1)

        return (img * 255).astype(np.uint8)
