import cv2
import numpy as np

def generate_lut(points):
    xs, ys = zip(*sorted(points))
    ys = [255 - y for y in ys]  # Invert to match brightness
    lut = np.interp(np.arange(256), xs, ys)
    return np.clip(lut, 0, 255).astype(np.uint8)

def apply_curve(img, lut):
    r, g, b = cv2.split(img)
    r = cv2.LUT(r, lut)
    g = cv2.LUT(g, lut)
    b = cv2.LUT(b, lut)
    return cv2.merge((r, g, b))

# def add_point(event):
#     if event.state & 0x0004:  # Ctrl key on Windows/Linux
#         self.points.append((event.x, event.y))
#         self.draw_curve()

# def move_point(event):
#     closest = min(self.points, key=lambda p: abs(p[0] - event.x))
#     self.points.remove(closest)
#     self.points.append((event.x, event.y))
#     self.draw_curve()

# End Curve