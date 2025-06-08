from numba import njit
import numpy as np
import cv2


def adjust_shadows_lights(img, shadow_factor=1.0, light_factor=1.0):
    lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    l_modified = fast_adjust_l_channel(l, shadow_factor, light_factor)
    adjusted_lab = cv2.merge((l_modified, a, b))
    return cv2.cvtColor(adjusted_lab, cv2.COLOR_LAB2RGB)


@njit
def fast_adjust_l_channel(l, shadow_factor, light_factor):
    l_modified = l.astype(np.float32)
    for i in range(l.shape[0]):
        for j in range(l.shape[1]):
            value = l[i, j] / 255.0  # Normalize to 0-1
            # Smooth blending based on value position between shadow/light
            blend = 1.0 / (1.0 + np.exp(-12 * (value - 0.5)))  # sigmoid centered at 0.5
            factor = shadow_factor * (1 - blend) + light_factor * blend
            l_modified[i, j] *= factor
    l_modified = np.clip(l_modified, 0, 255).astype(np.uint8)
    return l_modified
