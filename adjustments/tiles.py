# import numpy as np
# import cv2
# from concurrent.futures import ThreadPoolExecutor

# from .brightness import apply_brightness
# from .contrast import apply_contrast
# from .saturation import adjust_saturation_rgb
# from .curve import *
# from .shadows_lights import adjust_shadows_lights
# from .white_balance import *
# from .dehaze import dehaze_effect
# from .fog import fog_effect
# from .hsl import *

# def split_image_into_tiles(img):
#     num_tiles=8
#     print('----------- split_image_into_tiles ---------------')
#     h, w = img.shape[:2]
#     tile_height = h // num_tiles
#     tiles = []
#     for i in range(num_tiles):
#         y_start = i * tile_height
#         y_end = (i + 1) * tile_height if i < num_tiles - 1 else h
#         tiles.append(img[y_start:y_end].copy())
#     return tiles

# def merge_tiles_back(tiles):
#     print('----------- merge_tiles_back ---------------')
#     return np.vstack(tiles)


# def process_tile(tile, tipo):
#     try:

#         if tipo == 'temperature':
#             print('--- temperature:')
#             tile = apply_kelvin_temperature(tile, tipo)
#             print("After temperature:", tile.shape)
#             return tile

#         if tipo == 'tint':
#             print('--- tint:')
#             tile = apply_tint_shift(tile, tipo)
#             print("After tint:", tile.shape)
#             return tile

#         if tipo == 'brightness':
#             print('--- brightness:')
#             tile = apply_brightness(tile, tipo)
#             print("After brightness:", tile.shape)
#             return tile

#         if tipo == 'contrast':
#             print('--- contrast:')
#             tile = apply_contrast(tile, tipo)
#             print("After contrast:", tile.shape)
#             return tile

#         if tipo == 'saturation':
#             print('--- saturation:')
#             tile = adjust_saturation_rgb(tile, tipo)
#             print("After saturation:", tile.shape)
#             return tile

#         if tipo == 'saturation':
#             print('--- saturation:')
#             tile = adjust_saturation_rgb(tile, tipo)
#             print("After saturation:", tile.shape)
#             return tile

#         if tipo == 'shadow_factor':
#             print('--- shadow_factor:')
#             tile = adjust_shadows_lights(tile, tipo)
#             print("After shadow_factor:", tile.shape)
#             return tile

#         tile = adjust_shadows_lights(tile, adjustments['shadow_factor'], adjustments['light_factor'])

#         print("After shadows/lights:", tile.shape)

#         tile = dehaze_effect(tile, adjustments['dehaze'])

#         print("After dehaze:", tile.shape)

#         tile = fog_effect(tile, adjustments['fog'])

#         print("After fog:", tile.shape)

#         tile = apply_hsl_superfast(tile, adjustments['hue_adj'], adjustments['sat_adj'], adjustments['lum_adj'])

#         print("After hsl:", tile.shape)

#         return tile

#     except Exception as e:
#         print("Error in tile processing:", e)
#         return None


# # def process_tile(tile, adjustments):
# #     try:
# #         print('--- brightness:', adjustments['brightness'])
# #         tile = apply_kelvin_temperature(tile, adjustments['temperature'])

# #         tile = apply_tint_shift(tile, adjustments['tint'])

# #         tile = apply_brightness(tile, adjustments['brightness'])

# #         print("After brightness:", tile.shape)

# #         tile = apply_contrast(tile, adjustments['contrast'])

# #         print("After contrast:", tile.shape)

# #         tile = adjust_saturation_rgb(tile, adjustments['saturation'])

# #         print("After saturation:", tile.shape)

# #         tile = adjust_shadows_lights(tile, adjustments['shadow_factor'], adjustments['light_factor'])

# #         print("After shadows/lights:", tile.shape)

# #         tile = dehaze_effect(tile, adjustments['dehaze'])

# #         print("After dehaze:", tile.shape)

# #         tile = fog_effect(tile, adjustments['fog'])

# #         print("After fog:", tile.shape)

# #         tile = apply_hsl_superfast(tile, adjustments['hue_adj'], adjustments['sat_adj'], adjustments['lum_adj'])

# #         print("After hsl:", tile.shape)

# #         return tile

# #     except Exception as e:
# #         print("Error in tile processing:", e)
# #         return None

