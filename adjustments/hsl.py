import numpy as np
import cv2
from numba import njit, prange


band_centers = [0, 11, 23, 45, 90, 108, 135, 162]  # in degrees
band_names = ['Red', 'Orange', 'Yellow', 'Green', 'Aqua', 'Blue', 'Purple', 'Magenta']

def assign_hue_band_map():
    hue_band = np.zeros(180, dtype=np.uint8)
    for i, center in enumerate(band_centers):
        for h in range(180):
            d = abs(h - center)
            wrap = min(d, 180 - d)
            if wrap < 7:
                hue_band[h] = i + 1  # 1-based band index (0 = no match)
    return hue_band

def generate_full_luts(hue_adj, sat_adj, lum_adj):
    hue_lut = np.arange(180, dtype=np.uint8)
    sat_luts = np.tile(np.arange(256), (8, 1))
    lum_luts = np.tile(np.arange(256), (8, 1))

    for i, name in enumerate(band_names):
        h_shift = hue_adj.get(name, 0)
        s_shift = sat_adj.get(name, 0)
        l_shift = lum_adj.get(name, 0)

        hue_lut = (hue_lut + np.where(assign_hue_band_map() == (i + 1), h_shift, 0)) % 180

        sat_luts[i] = np.clip(np.arange(256) + s_shift, 0, 255)
        lum_luts[i] = np.clip(np.arange(256) + l_shift, 0, 255)

    return hue_lut.astype(np.uint8), sat_luts.astype(np.uint8), lum_luts.astype(np.uint8), assign_hue_band_map()


def apply_hsl_superfast(img_bgr, hue_adj, sat_adj, lum_adj):
    hue_lut, sat_luts, lum_luts, hue_band = generate_full_luts(hue_adj, sat_adj, lum_adj)

    hls = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HLS)
    h, l, s = cv2.split(hls)

    band_indices = hue_band[h]

    # Apply LUTs based on band
    h_new = hue_lut[h]
    s_new = s.copy()
    l_new = l.copy()

    for i in range(1, 9):  # band 1 to 8
        mask = band_indices == i
        s_new[mask] = sat_luts[i - 1][s[mask]]
        l_new[mask] = lum_luts[i - 1][l[mask]]

    result_hls = cv2.merge((h_new, l_new, s_new))
    return cv2.cvtColor(result_hls, cv2.COLOR_HLS2BGR)








# def create_hue_band_lut():
#     band_centers = [0, 11, 23, 45, 90, 108, 135, 162]  # in degrees
#     hue_lut = np.zeros(180, dtype=np.uint8)

#     for i, center in enumerate(band_centers):
#         for h in range(180):
#             d = abs(h - center)
#             wrap = min(d, 180 - d)
#             if wrap < 7:  # 14° range
#                 hue_lut[h] = i + 1  # 1-based band index (0 means no band)
#     return hue_lut


# @njit(parallel=True)
# def apply_hsl_core_lut(hls_img, hue_lut, hue_adj, sat_adj, lum_adj):
#     h, w, _ = hls_img.shape
#     for y in prange(h):
#         for x in range(w):
#             h_val, l_val, s_val = hls_img[y, x]
#             band = hue_lut[int(h_val)]
#             if band == 0:
#                 continue  # no band match
#             idx = band - 1

#             h_val = (h_val + hue_adj[idx]) % 180
#             s_val = min(max(s_val + sat_adj[idx], 0), 255)
#             l_val = min(max(l_val + lum_adj[idx], 0), 255)

#             hls_img[y, x] = [h_val, l_val, s_val]
#     return hls_img

