import cv2
import numpy as np

def adjust_saturation_rgb(img, saturation):
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    gray = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
    return cv2.addWeighted(img, saturation, gray, 1 - saturation, 0)
