import cv2, numpy as np 

def apply_hsl_adjustments(img, hue_adj, sat_adj, lum_adj):
    img_hls = cv2.cvtColor(img, cv2.COLOR_BGR2HLS).astype(np.float32)
    h, l, s = cv2.split(img_hls)

    # Normalize to 0-1
    h /= 180.0
    l /= 255.0
    s /= 255.0

    # Hue band centers in normalized hue space
    band_centers = {
        "Red": 0.0,
        "Orange": 0.06,
        "Yellow": 0.13,
        "Green": 0.25,
        "Aqua": 0.5,
        "Blue": 0.6,
        "Purple": 0.75,
        "Magenta": 0.9,
    }

    for color, center in band_centers.items():
        # Create a mask for the band
        dist = np.abs(h - center)
        dist = np.minimum(dist, 1 - dist)  # wrap-around distance
        mask = dist < 0.04  # soft band ~14.4 degrees
        strength = 1.0 - (dist / 0.04)
        strength = np.clip(strength, 0, 1)

        # Apply Hue shift
        h[mask] += hue_adj.get(color, 0) / 360.0 * strength[mask]
        h %= 1.0

        # Saturation and luminance
        s[mask] += sat_adj.get(color, 0) * strength[mask]
        l[mask] += lum_adj.get(color, 0) * strength[mask]

    # Clip and convert back
    h = np.clip(h * 180, 0, 180)
    l = np.clip(l * 255, 0, 255)
    s = np.clip(s * 255, 0, 255)

    adjusted = cv2.merge((h, l, s)).astype(np.uint8)
    return cv2.cvtColor(adjusted, cv2.COLOR_HLS2BGR)






# import numpy as np
# import cv2
# from numba import njit, prange

# @njit(parallel=True)
# def apply_hsl_core(hls_img, hue_adj, sat_adj, lum_adj):
#     h, w, _ = hls_img.shape
#     for y in prange(h):
#         for x in range(w):
#             h_val, l_val, s_val = hls_img[y, x]

#             # Hue shift by color range (simplified to example color bands)
#             if 0 <= h_val < 20:   # Red
#                 h_val = (h_val + hue_adj[0]) % 180
#                 s_val = np.clip(s_val * sat_adj[0], 0, 255)
#                 l_val = np.clip(l_val * lum_adj[0], 0, 255)
#             elif 20 <= h_val < 40:  # Orange
#                 h_val = (h_val + hue_adj[1]) % 180
#                 s_val = np.clip(s_val * sat_adj[1], 0, 255)
#                 l_val = np.clip(l_val * lum_adj[1], 0, 255)
#             # ...continue for Yellow, Green, Aqua, Blue, Purple, Magenta...

#             hls_img[y, x] = [h_val, l_val, s_val]
#     return hls_img

# def apply_hsl_adjustments(img, hue_adj_dict, sat_adj_dict, lum_adj_dict):
#     hls = cv2.cvtColor(img, cv2.COLOR_BGR2HLS).astype(np.float32)

#     hue_adj = np.array([hue_adj_dict[color] for color in ['red', 'orange', 'yellow', 'green', 'aqua', 'blue', 'purple', 'magenta']], dtype=np.float32)
#     sat_adj = np.array([sat_adj_dict[color] for color in ['red', 'orange', 'yellow', 'green', 'aqua', 'blue', 'purple', 'magenta']], dtype=np.float32)
#     lum_adj = np.array([lum_adj_dict[color] for color in ['red', 'orange', 'yellow', 'green', 'aqua', 'blue', 'purple', 'magenta']], dtype=np.float32)

#     hls = apply_hsl_core(hls, hue_adj, sat_adj, lum_adj)
#     result = cv2.cvtColor(hls.astype(np.uint8), cv2.COLOR_HLS2BGR)
#     return result

