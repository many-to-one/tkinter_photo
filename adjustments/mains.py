import numpy as np
import cv2

# def apply_adjustments_(img, brightness, contrast, saturation, shadow_factor, highlight_factor, temperature, tint, hsl_h, hsl_s, hsl_l):

#     print(' --------------------------- apply_adjustments_ --------------------------- ', hsl_h, hsl_s, hsl_l)
#     # Convert to float for precision
#     img = img.astype(np.float32) / 255.0

#     # Split channels
#     r, g, b = cv2.split(img)

#     # Apply brightness
#     r += brightness / 255.0
#     g += brightness / 255.0
#     b += brightness / 255.0

#     # Apply contrast
#     r = (r - 0.5) * contrast + 0.5
#     g = (g - 0.5) * contrast + 0.5
#     b = (b - 0.5) * contrast + 0.5

#     # Apply white balance
#     r += temperature / 255.0
#     b -= temperature / 255.0
#     g += tint / 255.0

#     # Apply shadows/highlights
#     luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
#     factor = np.where(luminance < 0.5, shadow_factor, highlight_factor)
#     r *= factor
#     g *= factor
#     b *= factor

#     # Apply saturation
#     avg = (r + g + b) / 3.0
#     r = avg + (r - avg) * saturation
#     g = avg + (g - avg) * saturation
#     b = avg + (b - avg) * saturation

#     # Convert RGB to HSL and apply HSL adjustments
#     img_hsl = cv2.cvtColor((img * 255).astype(np.uint8), cv2.COLOR_RGB2HLS).astype(np.float32) / 255.0
#     h, l, s = cv2.split(img_hsl)

#     # Determine color bands
#     band = np.clip((h * 6).astype(int), 0, 5)
    
#     # s *= hsl_s[band]
#     # l *= hsl_l[band]
#     # h += hsl_h[band]
#     # h = np.mod(h, 1.0)  # Wrap around 0–1

#     s *= np.take(hsl_s, band)
#     l *= np.take(hsl_l, band)
#     h += np.take(hsl_h, band)



#     # Convert back to RGB
#     img_hsl = cv2.merge([h, l, s])
#     img_rgb = cv2.cvtColor((img_hsl * 255).astype(np.uint8), cv2.COLOR_HLS2RGB)

#     return img_rgb



def apply_adjustments_(img, brightness, contrast, saturation, shadow_factor, highlight_factor, temperature, tint, hsl_h, hsl_s, hsl_l):
# def apply_adjustments_(img, brightness, contrast, saturation, shadow_factor, highlight_factor, temperature, tint):
    print(' --------------------------- apply_adjustments_ --------------------------- ', hsl_h, hsl_s, hsl_l)

    # Convert to float for precision
    img = img.astype(np.float32) / 255.0
    img = np.clip(img, 0, 1)  # Ensure pixel values stay within valid range

    # Split channels
    r, g, b = cv2.split(img)

    # Apply brightness
    r += brightness / 255.0
    g += brightness / 255.0
    b += brightness / 255.0

    # Apply contrast
    r = (r - 0.5) * contrast + 0.5
    g = (g - 0.5) * contrast + 0.5
    b = (b - 0.5) * contrast + 0.5

    # Apply white balance
    r += temperature / 255.0
    b -= temperature / 255.0
    g += tint / 255.0

    # Apply shadows/highlights
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    factor = np.where(luminance < 0.5, shadow_factor, highlight_factor)
    r *= factor
    g *= factor
    b *= factor

    # Apply saturation
    avg = (r + g + b) / 3.0
    r = avg + (r - avg) * saturation
    g = avg + (g - avg) * saturation
    b = avg + (b - avg) * saturation

    # Convert RGB to HSL and apply HSL adjustments
    img_hsl = cv2.cvtColor((img * 255).astype(np.uint8), cv2.COLOR_RGB2HLS).astype(np.float32) / 255.0
    h, l, s = cv2.split(img_hsl)

    # Determine color bands
    band_centers = np.array([0, 11, 23, 45, 90, 108, 135, 162]) / 360.0  # Normalize to 0-1 range

    # Compute closest band
    # band = np.argmin(np.abs(h[:, :] - band_centers[:, None, None]), axis=0)
    band = np.clip((h * 6).astype(int), 0, 5)

    # Apply adjustments
    s *= np.take(hsl_s, band)
    l *= np.take(hsl_l, band)
    h += np.take(hsl_h, band)
    h = np.mod(h, 1.0)  # Wrap around 0–1


    # band = np.clip((h * 6).astype(int), 0, 5)

    # print("s shape:", s.shape)
    # print("band shape:", band.shape)
    # print("hsl_s shape:", np.array(hsl_s).shape)


    # s *= np.take(hsl_s, band) 
    # l *= np.take(hsl_l, band) 
    # h += np.take(hsl_h, band) 
    # h = np.mod(h, 1.0) # Wrap around 0–1


    # Convert back to RGB
    img_hsl = cv2.merge([h, l, s])
    img_rgb = cv2.cvtColor((img_hsl * 255).astype(np.uint8), cv2.COLOR_HLS2RGB)

    # Ensure final pixel values are valid
    img_rgb = np.clip(img_rgb, 0, 255).astype(np.uint8)

    return img_rgb



# # Example usage
# image = cv2.imread("example.jpg")
# adjusted_image = apply_adjustments(image, 20, 1.2, 1.1, 1.2, 0.8, 10, -5, [0.1]*6, [1.2]*6, [1.0]*6)
# cv2.imwrite("output.jpg", adjusted_image)
