import cv2

def dehaze_effect(img, strength):
        if strength == 0:
            return img

        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        # print(' ------ dehaze_image ------', strength)

        clahe = cv2.createCLAHE(clipLimit=2.0 + 4.0 * strength, tileGridSize=(8, 8))
        cl = clahe.apply(l)

        merged = cv2.merge((cl, a, b))
        return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)