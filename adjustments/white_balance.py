import numpy as np
import cv2

def apply_white_balance_eyedropper(image, target_pixel):
    # Extract R, G, B values
    b, g, r = target_pixel.astype(float)

    # Compute gain factors to equalize the RGB channels
    avg = (r + g + b) / 3.0
    gain_r = avg / r
    gain_g = avg / g
    gain_b = avg / b

    # Apply gain to each channel
    b_img, g_img, r_img = cv2.split(image.astype(float))
    b_img *= gain_b
    g_img *= gain_g
    r_img *= gain_r

    # Clip values and merge
    balanced_img = cv2.merge([
        np.clip(b_img, 0, 255).astype(np.uint8),
        np.clip(g_img, 0, 255).astype(np.uint8),
        np.clip(r_img, 0, 255).astype(np.uint8)
    ])
    return balanced_img

# Predefined RGB values for temperatures
kelvin_table = {
    1000: (255, 56, 0),
    2000: (255, 138, 18),
    3000: (255, 180, 107),
    4000: (255, 209, 163),
    5000: (255, 228, 206),
    6500: (255, 249, 253),
    7500: (245, 243, 255),
    10000: (235, 238, 255)
}

def apply_kelvin_temperature(image, kelvin):
    # Clamp and interpolate RGB multipliers
    kelvin = max(1000, min(10000, kelvin))
    keys = sorted(kelvin_table)
    for i in range(len(keys)-1):
        if keys[i] <= kelvin <= keys[i+1]:
            k1, k2 = keys[i], keys[i+1]
            ratio = (kelvin - k1) / (k2 - k1)
            r1, g1, b1 = kelvin_table[k1]
            r2, g2, b2 = kelvin_table[k2]
            r = r1 + (r2 - r1) * ratio
            g = g1 + (g2 - g1) * ratio
            b = b1 + (b2 - b1) * ratio
            break
    else:
        r, g, b = kelvin_table[keys[-1]]

    # Normalize gains to 1.0 base
    r_gain = 255.0 / r
    g_gain = 255.0 / g
    b_gain = 255.0 / b

    # Apply gains
    b_img, g_img, r_img = cv2.split(image.astype(float))
    b_img *= b_gain
    g_img *= g_gain
    r_img *= r_gain

    result = cv2.merge([
        np.clip(b_img, 0, 255).astype(np.uint8),
        np.clip(g_img, 0, 255).astype(np.uint8),
        np.clip(r_img, 0, 255).astype(np.uint8)
    ])
    return result


def apply_tint_shift(image, tint_shift):
    """
    Applies a green ↔ magenta tint shift.
    Positive = more magenta, Negative = more green
    """
    b, g, r = cv2.split(image.astype(np.int16))  # prevent overflow

    # Tint shift = adjust R and G inversely
    g = g - tint_shift
    r = r + tint_shift

    # Clip and merge
    g = np.clip(g, 0, 255)
    r = np.clip(r, 0, 255)
    image = cv2.merge([b.astype(np.uint8), g.astype(np.uint8), r.astype(np.uint8)])
    return image
