import colorsys
from numba import njit, prange
import numpy as np


@njit(parallel=True)
def apply_primary_calibration_rgb(image, hue_r, hue_g, hue_b, sat_r, sat_g, sat_b):

    h, w, _ = image.shape
    for y in prange(h):
        for x in range(w):
            r, g, b = image[y, x] / 255.0

            # Full RGB to HSV
            h1, s1, v1 = rgb_to_hsv(r, g, b)

            # Estimate how much the pixel belongs to each primary
            total = r + g + b + 1e-6  # avoid division by zero
            red_weight = r / total
            green_weight = g / total
            blue_weight = b / total

            # Combined hue and sat shifts weighted by influence
            hue_shift = hue_r * red_weight + hue_g * green_weight + hue_b * blue_weight
            sat_mult = (
                sat_r * red_weight +
                sat_g * green_weight +
                sat_b * blue_weight
            )

            # Apply shift
            h1 = (h1 + hue_shift) % 1.0
            s1 = min(max(s1 * sat_mult, 0.0), 1.0)

            r1, g1, b1 = hsv_to_rgb(h1, s1, v1)
            image[y, x] = np.array([r1, g1, b1]) * 255.0

    print(' ----------- apply_primary_calibration_rgb HERE ### --------------')
    return image.astype(np.uint8)


@njit(parallel=True)
def apply_shadow_calibration_rgb(
    image, shadow_hue_r, shadow_hue_g, shadow_hue_b,
    shadow_sat_r, shadow_sat_g, shadow_sat_b,
    shadow_range=0.3
):

    h, w, _ = image.shape
    for y in prange(h):
        for x in range(w):
            r, g, b = image[y, x] / 255.0

            # Luminance to find shadows
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            if lum < shadow_range:
                weight = 1.0 - (lum / shadow_range)  # 1 at black, 0 at shadow_range

                # Compute HSV
                h1, s1, v1 = rgb_to_hsv(r, g, b)

                total = r + g + b + 1e-6
                rw = r / total
                gw = g / total
                bw = b / total

                # Weighted hue/sat shifts based on RGB dominance
                hue_shift = (
                    shadow_hue_r * rw +
                    shadow_hue_g * gw +
                    shadow_hue_b * bw
                )

                sat_mult = (
                    shadow_sat_r * rw +
                    shadow_sat_g * gw +
                    shadow_sat_b * bw
                )

                # Apply with strength modulated by luminance
                h1 = (h1 + hue_shift * weight) % 1.0
                s1 = min(max(s1 * (1.0 + (sat_mult - 1.0) * weight), 0.0), 1.0)

                r1, g1, b1 = hsv_to_rgb(h1, s1, v1)
                image[y, x] = np.array([r1, g1, b1]) * 255.0

    print(' ----------- apply_shadow_calibration_rgb HERE ### --------------')

    return image.astype(np.uint8)


@njit()
def rgb_to_hsv(r, g, b):
    maxc = max(r, g, b)
    minc = min(r, g, b)
    v = maxc
    if minc == maxc:
        return 0.0, 0.0, v
    s = (maxc - minc) / maxc
    rc = (maxc - r) / (maxc - minc)
    gc = (maxc - g) / (maxc - minc)
    bc = (maxc - b) / (maxc - minc)
    if r == maxc:
        h = bc - gc
    elif g == maxc:
        h = 2.0 + rc - bc
    else:
        h = 4.0 + gc - rc
    h = (h / 6.0) % 1.0
    return h, s, v

@njit()
def hsv_to_rgb(h, s, v):
    if s == 0.0:
        return v, v, v
    i = int(h * 6.0)
    f = (h * 6.0) - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    i = i % 6
    if i == 0:
        return v, t, p
    if i == 1:
        return q, v, p
    if i == 2:
        return p, v, t
    if i == 3:
        return p, q, v
    if i == 4:
        return t, p, v
    if i == 5:
        return v, p, q
    return 0.0, 0.0, 0.0