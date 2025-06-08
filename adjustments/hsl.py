import numpy as np
import cv2
from numba import njit, prange


def assign_soft_hue_weights(sigma=7):
    hue_weights = np.zeros((180, len(band_centers)), dtype=np.float32)
    for h in range(180):
        total_weight = 0.0
        for i, center in enumerate(band_centers):
            d = abs(h - center)
            wrap = min(d, 180 - d)
            w = np.exp(-(wrap**2) / (2 * sigma**2))
            hue_weights[h, i] = w
            total_weight += w
        hue_weights[h, :] /= total_weight  # Normalize
    return hue_weights  # shape: (180, 8)


@njit(parallel=True)
def apply_hsl_core_lut_soft(hls_img, hue_weights, hue_adj_arr, sat_adj_arr, lum_adj_arr):
    h, w, _ = hls_img.shape
    for y in prange(h):
        for x in range(w):
            h_val, l_val, s_val = hls_img[y, x]
            h_idx = int(h_val)
            # Smooth adjustment based on weights
            h_adjust = 0.0
            s_adjust = 0.0
            l_adjust = 0.0
            for i in range(hue_weights.shape[1]):
                weight = hue_weights[h_idx, i]
                h_adjust += hue_adj_arr[i] * weight
                s_adjust += sat_adj_arr[i] * weight
                l_adjust += lum_adj_arr[i] * weight

            new_h = (h_val + h_adjust) % 180
            new_s = min(max(s_val + s_adjust, 0), 255)
            new_l = min(max(l_val + l_adjust, 0), 255)

            hls_img[y, x] = [new_h, new_l, new_s]
    return hls_img


def apply_hsl_superfast(img_bgr, hue_adj, sat_adj, lum_adj):

    hue_adj = normalize_keys(hue_adj)
    sat_adj = normalize_keys(sat_adj)
    lum_adj = normalize_keys(lum_adj)

    hue_adj_arr = np.array([hue_adj.get(b, 0) for b in band_names], dtype=np.float32)
    sat_adj_arr = np.array([sat_adj.get(b, 0) for b in band_names], dtype=np.float32)
    lum_adj_arr = np.array([lum_adj.get(b, 0) for b in band_names], dtype=np.float32)

    print(' --------------- hue_adj_arr --------------- ', hue_adj_arr)
    print(' --------------- sat_adj_arr --------------- ', sat_adj_arr)
    print(' --------------- lum_adj_arr --------------- ', lum_adj_arr)

    hue_weights = assign_soft_hue_weights()  # shape: (180, 8)

    hls = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HLS).astype(np.float32)
    hls = apply_hsl_core_lut_soft(hls, hue_weights, hue_adj_arr, sat_adj_arr, lum_adj_arr)
    return cv2.cvtColor(hls.astype(np.uint8), cv2.COLOR_HLS2BGR)



band_centers = [0, 11, 23, 45, 90, 108, 135, 162]  # in degrees
band_names = ['Red', 'Orange', 'Yellow', 'Green', 'Aqua', 'Blue', 'Purple', 'Magenta']



def normalize_keys(d):
    return {k.capitalize(): v for k, v in d.items()}  # Ensures first letter uppercase



# --------------------------------------------------------------------------------------- #
#       Without midtones and another colors atach, only current collor edition            #
# --------------------------------------------------------------------------------------- #


# @njit(parallel=True)
# def apply_hsl_core_lut(hls_img, hue_band_lut, hue_adj_arr, sat_adj_arr, lum_adj_arr):
#     print(' --------------- hue_adj_arr --------------- ', hue_adj_arr)
#     print(' --------------- sat_adj_arr --------------- ', sat_adj_arr)
#     print(' --------------- lum_adj_arr --------------- ', lum_adj_arr)
#     h, w, _ = hls_img.shape
#     for y in prange(h):
#         for x in range(w):
#             h_val, l_val, s_val = hls_img[y, x]
#             band = hue_band_lut[int(h_val)]
#             if band == 0:
#                 continue
#             idx = band - 1
#             h_val = (h_val + hue_adj_arr[idx]) % 180
#             s_val = min(max(s_val + sat_adj_arr[idx], 0), 255)
#             l_val = min(max(l_val + lum_adj_arr[idx], 0), 255)
#             hls_img[y, x] = [h_val, l_val, s_val]
#     return hls_img




# def apply_hsl_superfast(img_bgr, hue_adj, sat_adj, lum_adj):

#     print(' ------------------ hue_adj: ------------------ ', hue_adj)
#     print(' ------------------ sat_adj: ------------------ ', sat_adj)
#     print(' ------------------ lum_adj: ------------------ ', lum_adj)

#     hue_adj = normalize_keys(hue_adj)
#     sat_adj = normalize_keys(sat_adj)
#     lum_adj = normalize_keys(lum_adj)

#     hue_adj_arr = np.array([hue_adj.get(b, 0) for b in band_names], dtype=np.int16)
#     sat_adj_arr = np.array([sat_adj.get(b, 0) for b in band_names], dtype=np.int16)
#     lum_adj_arr = np.array([lum_adj.get(b, 0) for b in band_names], dtype=np.int16)

#     hue_band_lut = assign_hue_band_map()

#     hls = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HLS).astype(np.float32)
#     hls = apply_hsl_core_lut(hls, hue_band_lut, hue_adj_arr, sat_adj_arr, lum_adj_arr)
#     return cv2.cvtColor(hls.astype(np.uint8), cv2.COLOR_HLS2BGR)


# def assign_hue_band_map():
#     hue_band = np.zeros(180, dtype=np.uint8)
#     for i, center in enumerate(band_centers):
#         for h in range(180):
#             d = abs(h - center)
#             wrap = min(d, 180 - d)
#             if wrap < 7:
#                 hue_band[h] = i + 1  # 1-based band index (0 = no match)
#     return hue_band

