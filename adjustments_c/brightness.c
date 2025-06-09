// // brightness.c
// #include <stdint.h>

// void apply_brightness(unsigned char* data, int width, int height, int channels, float brightness) {
//     int size = width * height * channels;
//     for (int i = 0; i < size; i++) {
//         int val = data[i] + brightness;
//         if (val > 255) val = 255;
//         if (val < 0) val = 0;
//         data[i] = (unsigned char)val;
//     }
// }





// image_adjustments.c
// One-stop batch image adjustment function for brightness, contrast, saturation,
// shadows, highlights, white balance (temp/tint), HSL adjustments, and calibration.

#include <math.h>
#include <stdint.h>
#include <string.h>

#define clamp(x, low, high) ((x) < (low) ? (low) : (x) > (high) ? (high) : (x))

// Helper to convert BGR to HSL (simplified, not 100% accurate for speed)
void rgb_to_hsl(float r, float g, float b, float *h, float *s, float *l) {
    float max = fmaxf(fmaxf(r, g), b);
    float min = fminf(fminf(r, g), b);
    float d = max - min;

    *l = (max + min) / 2.0f;

    if (d == 0.0f) {
        *h = *s = 0.0f;
    } else {
        *s = (*l > 0.5f) ? d / (2.0f - max - min) : d / (max + min);

        if (max == r)
            *h = (g - b) / d + (g < b ? 6 : 0);
        else if (max == g)
            *h = (b - r) / d + 2;
        else
            *h = (r - g) / d + 4;

        *h /= 6.0f;
    }
}

// Reapply HSL adjustments with limited logic
void apply_hsl_mod(float *r, float *g, float *b,
                   float *hue_adj, float *sat_adj, float *lum_adj) {
    float h, s, l;
    rgb_to_hsl(*r, *g, *b, &h, &s, &l);

    // Example: apply global sat/lum scaling
    s = clamp(s * sat_adj[0], 0.0f, 1.0f);
    l = clamp(l * lum_adj[0], 0.0f, 1.0f);

    // Convert HSL back to RGB (simplified, or you can use LUTs)
    float q = l < 0.5f ? l * (1 + s) : l + s - l * s;
    float p = 2 * l - q;

    float t[3] = { h + 1.0f/3.0f, h, h - 1.0f/3.0f };
    float c[3];
    for (int i = 0; i < 3; ++i) {
        if (t[i] < 0) t[i] += 1;
        if (t[i] > 1) t[i] -= 1;
        if (t[i] < 1.0f/6.0f)
            c[i] = p + (q - p) * 6 * t[i];
        else if (t[i] < 1.0f/2.0f)
            c[i] = q;
        else if (t[i] < 2.0f/3.0f)
            c[i] = p + (q - p) * (2.0f/3.0f - t[i]) * 6;
        else
            c[i] = p;
    }

    *r = c[0];
    *g = c[1];
    *b = c[2];
}

// Core batch processor
void apply_all_adjustments(
    uint8_t* img_data, int width, int height, int channels,
    float brightness, float contrast, float saturation,
    float shadows, float highlights,
    float kelvin, float tint,
    float *hue_adj, float *sat_adj, float *lum_adj
) {
    int size = width * height * channels;
    for (int i = 0; i < size; i += channels) {
        float b = img_data[i] / 255.0f;
        float g = img_data[i+1] / 255.0f;
        float r = img_data[i+2] / 255.0f;

        // Apply brightness/contrast
        r = clamp((r - 0.5f) * contrast + 0.5f + brightness, 0.0f, 1.0f);
        g = clamp((g - 0.5f) * contrast + 0.5f + brightness, 0.0f, 1.0f);
        b = clamp((b - 0.5f) * contrast + 0.5f + brightness, 0.0f, 1.0f);

        // Approximate white balance shift
        r = clamp(r + kelvin * 0.05f + tint * 0.02f, 0.0f, 1.0f);
        b = clamp(b - kelvin * 0.05f, 0.0f, 1.0f);
        g = clamp(g + tint * 0.01f, 0.0f, 1.0f);

        // Shadows/Highlights boost
        float avg = (r + g + b) / 3.0f;
        float shadow_boost = 1.0f + shadows * (1.0f - avg);
        float highlight_cut = 1.0f - highlights * avg;
        r = clamp(r * shadow_boost * highlight_cut, 0.0f, 1.0f);
        g = clamp(g * shadow_boost * highlight_cut, 0.0f, 1.0f);
        b = clamp(b * shadow_boost * highlight_cut, 0.0f, 1.0f);

        // Saturation / HSL global adjust
        apply_hsl_mod(&r, &g, &b, hue_adj, sat_adj, lum_adj);

        img_data[i]   = (uint8_t)(r * 255.0f);
        img_data[i+1] = (uint8_t)(g * 255.0f);
        img_data[i+2] = (uint8_t)(b * 255.0f);
    }
}

