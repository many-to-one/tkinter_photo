# import ctypes
# import numpy as np
# import os

# # Get the directory of the current file (brightness_c.py)
# current_dir = os.path.dirname(__file__)
# dll_path = os.path.join(current_dir, "brightness.dll")

# lib = ctypes.CDLL(dll_path)

# # Set the arg types
# lib.apply_brightness.argtypes = [
#     ctypes.POINTER(ctypes.c_ubyte),  # image data
#     ctypes.c_int,  # width
#     ctypes.c_int,  # height
#     ctypes.c_int,  # channels
#     ctypes.c_float   # brightness
# ]

# lib.apply_brightness.restype = None

# def apply_brightness_c(img: np.ndarray, brightness: float) -> np.ndarray:
#     h, w, c = img.shape
#     img_c = np.ascontiguousarray(img, dtype=np.uint8)
#     ptr = img_c.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte))

#     lib.apply_brightness(ptr, w, h, c, ctypes.c_float(brightness))
#     return img_c



import ctypes
import numpy as np
import os

# Load DLL
dll_path = os.path.join(os.path.dirname(__file__), "adjustments.dll")
lib = ctypes.CDLL(dll_path)

# Define argtypes
lib.apply_all_adjustments.argtypes = [
    ctypes.POINTER(ctypes.c_uint8), ctypes.c_int, ctypes.c_int,
    ctypes.c_float, ctypes.c_float, ctypes.c_float,
    ctypes.c_float, ctypes.c_float,
    ctypes.c_float, ctypes.c_float,
    ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float),
]

def apply_all_adjustments_c(img: np.ndarray, brightness, contrast, saturation,
                             shadow, highlight, temperature, tint,
                             hue_arr, sat_arr, lum_arr) -> np.ndarray:

    assert img.dtype == np.uint8 and img.ndim == 3 and img.shape[2] == 3
    h, w, _ = img.shape
    flat = img.ravel()

    print('----------- hue_arr ------------', hue_arr)
    print('----------- sat_arr ------------', sat_arr)
    print('----------- lum_arr ------------', lum_arr)
    print('----------- hue_arr ------------', brightness)

    h_arr = (ctypes.c_float * 6)(*hue_arr)
    s_arr = (ctypes.c_float * 6)(*sat_arr)
    l_arr = (ctypes.c_float * 6)(*lum_arr)

    lib.apply_all_adjustments(
        flat.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
        w, h,
        float(brightness), float(contrast), float(saturation),
        float(shadow), float(highlight),
        float(temperature), float(tint),
        h_arr, s_arr, l_arr
    )
    return img.copy()
