import cv2

def apply_brightness(img, brightness):
    return cv2.convertScaleAbs(img, beta=brightness)
