import cv2

from numba import njit, prange
import numpy as np

# @njit(parallel=True)
def apply_brightness(img, brightness):
    # print('----------- apply_brightness ---------------', brightness)
    return cv2.convertScaleAbs(img, beta=brightness)

    # out = np.empty_like(img)
    # for y in prange(img.shape[0]):
    #     for x in range(img.shape[1]):
    #         for c in range(3):
    #             val = img[y, x, c] + brightness
    #             out[y, x, c] = min(max(val, 0), 255)
    # return out
