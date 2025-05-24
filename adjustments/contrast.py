import cv2
from numba import njit
import numpy as np

def apply_contrast(img, contrast):
    return cv2.convertScaleAbs(img, alpha=contrast)

