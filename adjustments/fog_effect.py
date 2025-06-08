import cv2
import numpy as np
from adjustments.contrast import apply_contrast

def fog_effect(img, strength):

        """
        Adds a fog effect by blending the image with a white layer.
        fog_intensity: float between 0 (no fog) and 2.0 (max fog)
        """
        fog_intensity = np.clip(strength, 0.0, 2.0)

        # Create a white image
        fog_color = np.full_like(img, 255)

        # Blend original with white
        blend_strength = min(strength / 2.0, 1.0)
        fogged = cv2.addWeighted(img, 1 - blend_strength, fog_color, blend_strength, 0)

        # Optional: reduce contrast slightly
        if strength > 0.1:
            fogged = apply_contrast(fogged, 1.0 - (strength * 0.15))  # adjust as needed

        return fogged