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


        print(' ------------- on_mouse_drag ------------- ', self.drag_mode)
        self.apply_gradients(self.app.small_image.copy(), self.app.gradients)

    def on_mouse_up(self, event):
        self.drag_mode = None
        self.selected_gradient_index = None

    
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
        print(' --------------------- on_mouse_double_click --------------------- ')


    def calculate_rotation_handle(self, cx, cy, angle_deg, offset=50):
        # print(' --------------------- calculate_rotation_handle --------------------- ', cx, cy, angle_deg)
        angle_rad = math.radians(angle_deg)
        hx = int(cx + offset * math.cos(angle_rad - math.pi / 2))  # above center
        hy = int(cy + offset * math.sin(angle_rad - math.pi / 2))
        print(' --------------------- calculate_rotation_handle --------------------- ', hx, hy)
        return (hx, hy)


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


    def apply_gradients(self, img, gradients):
        img = img.astype(np.float32) / 255.0  # Normalize

        for g in gradients:
            if not g["start"] or not g["end"]:
                continue

            x0, y0 = g["start"]
            x1, y1 = g["end"]
            x0, x1 = sorted([int(x0), int(x1)])
            y0, y1 = sorted([int(y0), int(y1)])

            h, w = y1 - y0, x1 - x0
            if h <= 0 or w <= 0:
                continue

            # Get adjustments (example: contrast + brightness)
            temperature = g.get("temperature") 
            tint = g.get("tint")
            brightness = g.get("brightness")
            contrast = g.get("contrast") 

            print(' --------------------- apply_gradients ------------------', temperature, tint)

            # Build vertical fade gradient
            fade = np.linspace(1.0, 0.0, h).reshape(h, 1, 1)  # shape (h, 1, 1)

            region = img[y0:y1, x0:x1]  # shape (h, w, 3)

            # --- White balance adjustments ---
            # Temperature shift: warm (positive) = more red/yellow, cool (negative) = more blue
            temp_strength = 0.6  # increase to see stronger effect
            region[:, :, 0] += (-temperature * temp_strength) * fade[:, :, 0]  # Blue channel
            region[:, :, 2] += (temperature * temp_strength) * fade[:, :, 0]   # Red channel

            # Tint shift: green (-) to magenta (+)
            tint_strength = 0.6
            region[:, :, 1] += (tint * tint_strength) * fade[:, :, 0]          # Green channel
            region[:, :, 0] += (-tint * tint_strength * 0.5) * fade[:, :, 0]   # Blue for magenta
            region[:, :, 2] += (-tint * tint_strength * 0.5) * fade[:, :, 0]   # Red for magenta


            # Apply brightness
            region += brightness * fade

            # Apply contrast
            mean = 0.5
            region = (region - mean) * (1 + contrast * fade) + mean

            # Clip to valid range
            img[y0:y1, x0:x1] = np.clip(region, 0, 1)

        img = (img * 255).astype(np.uint8)

        self.app.display_image = img
        self.app.show_image(self.app.display_image)
