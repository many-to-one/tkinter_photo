from adjustments.brightness import apply_brightness
from adjustments.contrast import apply_contrast
from adjustments.saturation import adjust_saturation_rgb
from adjustments.curve import *
from adjustments.shadows_lights import adjust_shadows_lights
from adjustments.white_balance import *
from adjustments.dehaze_effect import dehaze_effect
from adjustments.fog_effect import fog_effect
from adjustments.hsl import *
from adjustments.tiles import *
from adjustments.camera_calibration import *

""" It's to slow, so I use it in main.py """

def apply_adjustments(
        img,
        tipo, 
        value, 
        high_res,

        # Tone
        brightness,
        contrast,
        shadow_factor,
        light_factor,
        saturation,
        dehaze,
        fog,

        # White balance
        temperature,
        tint,

        hue_sliders,
        sat_sliders,
        lum_sliders,

        primary_hue_sliders,
        primary_sat_sliders,
        shadow_hue_sliders,
        shadow_sat_sliders,
    ):

        print('----------- tipo ------------', tipo)
        print('----------- value ///// ------------', value)

        img = apply_kelvin_temperature(img, temperature)
        img = apply_tint_shift(img, tint)

        img = apply_brightness(img, brightness)
        img = apply_contrast(img, contrast)
        img = adjust_saturation_rgb(img, saturation)
        img = adjust_shadows_lights(img, shadow_factor, light_factor)
        img = dehaze_effect(img, dehaze)
        img = fog_effect(img, fog)

        hue_adj = {color: slider.get() for color, slider in hue_sliders.items()}
        sat_adj = {color: slider.get() for color, slider in sat_sliders.items()}
        lum_adj = {color: slider.get() for color, slider in lum_sliders.items()}

        img = apply_hsl_superfast(img, hue_adj, sat_adj, lum_adj)

        # print(' ----------- apply_hsl_superfast --------------', img.shape)      

        primary_hue = {
            "Red": primary_hue_sliders["Red"].get(),
            "Green": primary_hue_sliders["Green"].get(),
            "Blue": primary_hue_sliders["Blue"].get(),
        }
        primary_sat = {
            "Red": primary_sat_sliders["Red"].get(),
            "Green": primary_sat_sliders["Green"].get(),
            "Blue": primary_sat_sliders["Blue"].get(),
        }

        img = apply_primary_calibration_rgb(
            img,
            primary_hue["Red"], primary_hue["Green"], primary_hue["Blue"],
            primary_sat["Red"], primary_sat["Green"], primary_sat["Blue"]
        )

        shadow_hue = {
            color: shadow_hue_sliders[color].get() for color in ["Red", "Green", "Blue"]
        }
        shadow_sat = {
            color: shadow_sat_sliders[color].get() for color in ["Red", "Green", "Blue"]
        }

        img = apply_shadow_calibration_rgb(
            img,
            shadow_hue['Red'], shadow_hue['Green'], shadow_hue['Blue'],
            shadow_sat['Red'], shadow_sat['Green'], shadow_sat['Blue']
        )

        # print(' ----------- apply_shadow_hue_sat_smooth_rgb --------------', img.shape)


        # # Eyedropper
        # if hasattr(self, 'eyedropper_pixel') and self.eyedropper_pixel is not None:
        #     img = apply_white_balance_eyedropper(img, self.eyedropper_pixel)


        # # Curve
        # self.curve_base_image = img.copy()

        # lut = self.generate_lut()

        # b, g, r = cv2.split(img)
        # r = cv2.LUT(r, lut)
        # g = cv2.LUT(g, lut)
        # b = cv2.LUT(b, lut)
        # img = cv2.merge((b, g, r))

        return img