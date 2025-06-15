// adjustments.c
#include <stdint.h>
#include <math.h>
#include <stdlib.h>
#include <math.h>


float clamp(float val, float min_val, float max_val) {
    if (!isfinite(val)) return min_val;
    if (val < min_val) return min_val;
    if (val > max_val) return max_val;
    return val;
}


// RGB <-> HSL helpers
void rgb_to_hsl(float r, float g, float b, float *h, float *s, float *l) {
    float max = fmaxf(r, fmaxf(g, b));
    float min = fminf(r, fminf(g, b));
    *l = (max + min) / 2.0f;

    if (max == min) {
        *h = *s = 0.0f;
    } else {
        float d = max - min;
        *s = (*l > 0.5f) ? (d / (2.0f - max - min)) : (d / (max + min));
        if (max == r)
            *h = (g - b) / d + (g < b ? 6.0f : 0.0f);
        else if (max == g)
            *h = (b - r) / d + 2.0f;
        else
            *h = (r - g) / d + 4.0f;
        *h /= 6.0f;
    }
}


void apply_all_adjustments(
    uint8_t* img, int width, int height,
    float brightness, float contrast, float saturation,
    float shadow_factor, float highlight_factor,
    float temperature, float tint,
    float dehaze, float fog,
    float hsl_h[8], float hsl_s[8], float hsl_l[8],
    float shadows_tint,
    float red_hue, float green_hue, float blue_hue, 
    float red_sat, float green_sat, float blue_sat
) {
    int size = width * height * 3;

    for (int i = 0; i < size; i += 3) {

        float r = img[i + 2] / 255.0f;
        float g = img[i + 1] / 255.0f;
        float b = img[i + 0] / 255.0f;

        // Variables for shadows/highlights
        float lum = 0.2126f * r + 0.7152f * g + 0.0722f * b;
        float shadow_weight = clamp(1.0f - lum * 2.0f, 0.0f, 1.0f);

        // Shadows Tint
        g -= shadow_weight * shadows_tint * 0.1f;
        r += shadow_weight * shadows_tint * 0.05f;

        // ---- Brightness / Shadows / Temp ----
        r += brightness / 255.0f;
        g += brightness / 255.0f;
        b += brightness / 255.0f;

        // Shadows / Highlights with smooth transition
        float highlight_weight = 1.0f - shadow_weight;
        float factor = shadow_weight * shadow_factor + highlight_weight * highlight_factor;

        r *= factor;
        g *= factor;
        b *= factor;


        r += temperature / 255.0f;
        g += tint / 255.0f;
        b -= temperature / 255.0f;

        // Clamp before contrast
        r = clamp(r, 0.0f, 1.0f);
        g = clamp(g, 0.0f, 1.0f);
        b = clamp(b, 0.0f, 1.0f);

        // Contrast
        r = (r - 0.5f) * contrast + 0.5f;
        g = (g - 0.5f) * contrast + 0.5f;
        b = (b - 0.5f) * contrast + 0.5f;

        r = clamp(r, 0.0f, 1.0f);
        g = clamp(g, 0.0f, 1.0f);
        b = clamp(b, 0.0f, 1.0f);

        // ---- HSL Adjustments ----
        float h, s, l;
        rgb_to_hsl(r, g, b, &h, &s, &l);

        // Global saturation adjustment
        s = clamp(s * saturation, 0.0f, 1.0f);

        int band = (int)(h * 8.0f);
        band = clamp(band, 0, 7);

        if (s > 0.1f && l > 0.05f) {
            h += hsl_h[band] / 8.0f;
            if (h > 1.0f) h -= 1.0f;
            if (h < 0.0f) h += 1.0f;
        }

        s = clamp(s * hsl_s[band], 0.0f, 1.0f);
        l = clamp(l * hsl_l[band], 0.0f, 1.0f);

        // ---- Dehaze ----
        if (dehaze > 0.0f) {
            float haze = (1.0f - fabsf(l - 0.5f) * 2.0f);  // haze near midtones
            l = clamp(l - haze * dehaze, 0.0f, 1.0f);
        }

        // ---- Convert back to RGB ----
        float q = l < 0.5f ? l * (1 + s) : (l + s - l * s);
        float p = 2 * l - q;
        float t[3] = { h + 1.0f/3.0f, h, h - 1.0f/3.0f };
        float c[3];
        for (int j = 0; j < 3; ++j) {
            if (t[j] < 0) t[j] += 1;
            if (t[j] > 1) t[j] -= 1;
            if (t[j] < 1.0f / 6.0f)
                c[j] = p + (q - p) * 6.0f * t[j];
            else if (t[j] < 0.5f)
                c[j] = q;
            else if (t[j] < 2.0f / 3.0f)
                c[j] = p + (q - p) * (2.0f / 3.0f - t[j]) * 6.0f;
            else
                c[j] = p;
        }

        r = clamp(c[0], 0.0f, 1.0f);
        g = clamp(c[1], 0.0f, 1.0f);
        b = clamp(c[2], 0.0f, 1.0f);

        // ---- Apply Fog ----
        if (fog > 0.0f) {
            r = r * (1.0f - fog) + fog;
            g = g * (1.0f - fog) + fog;
            b = b * (1.0f - fog) + fog;
        }


        // Camera Calibration — Primary RGB
        // NOTE: Hue shifts implemented as small channel offsets
        float r_shift = red_hue * (g - b);
        float g_shift = green_hue * (b - r);
        float b_shift = blue_hue * (r - g);

        r += r_shift;
        g += g_shift;
        b += b_shift;

        // Saturation per primary
        r = 0.5f + (r - 0.5f) * red_sat;
        g = 0.5f + (g - 0.5f) * green_sat;
        b = 0.5f + (b - 0.5f) * blue_sat;

        r = clamp(r, 0.0f, 1.0f);
        g = clamp(g, 0.0f, 1.0f);
        b = clamp(b, 0.0f, 1.0f);


        // Final safety
        if (!isfinite(r)) r = 0.0f;
        if (!isfinite(g)) g = 0.0f;
        if (!isfinite(b)) b = 0.0f;

        img[i + 2] = (uint8_t)(r * 255.0f);
        img[i + 1] = (uint8_t)(g * 255.0f);
        img[i + 0] = (uint8_t)(b * 255.0f);
    }
}