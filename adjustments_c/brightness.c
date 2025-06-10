#include <stdint.h>
#include <math.h>
#include <stdlib.h>

float clamp(float val, float min_val, float max_val) {
    return fmaxf(min_val, fminf(max_val, val));
}

// Helper to convert RGB [0-1] to HSL [0-1]
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

// Helper to convert HSL [0-1] back to RGB [0-1]
void hsl_to_rgb(float h, float s, float l, float *r, float *g, float *b) {
    if (s == 0.0f) {
        *r = *g = *b = l;
        return;
    }
    float q = l < 0.5f ? l * (1 + s) : l + s - l * s;
    float p = 2 * l - q;

    float t[3] = { h + 1.0f / 3.0f, h, h - 1.0f / 3.0f };
    for (int i = 0; i < 3; ++i) {
        if (t[i] < 0) t[i] += 1;
        if (t[i] > 1) t[i] -= 1;
    }

    float c[3];
    for (int i = 0; i < 3; ++i) {
        if (t[i] < 1.0f / 6.0f)
            c[i] = p + (q - p) * 6 * t[i];
        else if (t[i] < 1.0f / 2.0f)
            c[i] = q;
        else if (t[i] < 2.0f / 3.0f)
            c[i] = p + (q - p) * (2.0f / 3.0f - t[i]) * 6;
        else
            c[i] = p;
    }

    *r = c[0];
    *g = c[1];
    *b = c[2];
}

// Apply global HSL adjustment (single float for hue shift, sat scale, lum scale)
void apply_hsl_mod(float *r, float *g, float *b, float hue_adj, float sat_adj, float lum_adj) {
    // Normalize RGB to 0-1
    float rf = *r / 255.0f;
    float gf = *g / 255.0f;
    float bf = *b / 255.0f;

    float h, s, l;
    rgb_to_hsl(rf, gf, bf, &h, &s, &l);

    // Adjust hue by adding and wrapping around [0,1]
    h += hue_adj;
    if (h > 1.0f) h -= 1.0f;
    if (h < 0.0f) h += 1.0f;

    // Adjust saturation and luminance with clamp
    s = clamp(s * sat_adj, 0.0f, 1.0f);
    l = clamp(l * lum_adj, 0.0f, 1.0f);

    hsl_to_rgb(h, s, l, &rf, &gf, &bf);

    // Scale back to 0-255
    *r = rf * 255.0f;
    *g = gf * 255.0f;
    *b = bf * 255.0f;
}

void apply_all_adjustments(
    uint8_t* img, int width, int height,
    float brightness, float contrast, float saturation,
    float shadow_factor, float highlight_factor,
    float temperature, float tint,
    float hue_adj, float sat_adj, float lum_adj  // single global HSL adjustment params
) {
    int size = width * height * 3;
    float r, g, b;

    for (int i = 0; i < size; i += 3) {
        r = (float)img[i + 2];
        g = (float)img[i + 1];
        b = (float)img[i + 0];

        // Brightness
        r += brightness;
        g += brightness;
        b += brightness;

        // Contrast
        r = (r - 128.0f) * contrast + 128.0f;
        g = (g - 128.0f) * contrast + 128.0f;
        b = (b - 128.0f) * contrast + 128.0f;

        // Temperature/tint (simplified white balance)
        r += temperature;
        b -= temperature;
        g += tint;

        // Shadows/highlights
        float luminance = 0.2126f * r + 0.7152f * g + 0.0722f * b;
        if (luminance < 128.0f) {
            r *= shadow_factor;
            g *= shadow_factor;
            b *= shadow_factor;
        } else {
            r *= highlight_factor;
            g *= highlight_factor;
            b *= highlight_factor;
        }

        // Saturation (basic)
        float avg = (r + g + b) / 3.0f;
        r = avg + (r - avg) * saturation;
        g = avg + (g - avg) * saturation;
        b = avg + (b - avg) * saturation;

        // Apply global HSL adjustments
        apply_hsl_mod(&r, &g, &b, hue_adj, sat_adj, lum_adj);

        img[i + 2] = (uint8_t)clamp(r, 0, 255);
        img[i + 1] = (uint8_t)clamp(g, 0, 255);
        img[i + 0] = (uint8_t)clamp(b, 0, 255);
    }
}
