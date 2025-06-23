import cv2
import numpy as np

def apply_gradients(img, gradients):

    print(' --------------------- gradients --------------------- ', gradients)

    for g in gradients:
        if not g["start"] or not g["end"]:
            continue

        x0, y0 = g["start"]
        x1, y1 = g["end"]

        # Scale to original resolution if needed
        x0, x1 = sorted([int(x0), int(x1)])
        y0, y1 = sorted([int(y0), int(y1)])

        print('Gradient:', (x0, y0), 'to', (x1, y1))

        h, w = y1 - y0, x1 - x0
        if h <= 0 or w <= 0:
            continue  # Skip invalid

        # Draw gradient lines
        cv2.line(img, (x0, y0), (x1, y0), (255, 0, 0), 1)
        cv2.line(img, (x0, y1), (x1, y1), (255, 0, 0), 1)

        # Vertical gradient
        alpha = np.linspace(1.0, 0.0, h).reshape(-1, 1)

        # Blend effect into image
        for c in range(3):
            img[y0:y1, x0:x1, c] = img[y0:y1, x0:x1, c] * alpha

    return img