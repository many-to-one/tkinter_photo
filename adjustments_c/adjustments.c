// adjustments.c
#include <stdint.h>
#include <math.h>
#include <stdlib.h>

// float clamp(float val, float min_val, float max_val);

float clamp(float val, float min_val, float max_val) {
    return fmaxf(min_val, fminf(max_val, val));
}


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




// void apply_hsl_mod(float *r, float *g, float *b,
//                    float *hue_adj, float *sat_adj, float *lum_adj) {
//     float h, s, l;
//     rgb_to_hsl(*r, *g, *b, &h, &s, &l);

//     int band = (int)(h * 6.0f);
//     if (band >= 6) band = 5;

//     // Adjust hue with wrap-around
//     h += hue_adj[band];
//     if (h < 0) h += 1.0f;
//     if (h > 1) h -= 1.0f;

//     // Adjust saturation and luminance per band
//     s = clamp(s * sat_adj[band], 0.0f, 1.0f);
//     l = clamp(l * lum_adj[band], 0.0f, 1.0f);

//     // Convert HSL back to RGB
//     float q = l < 0.5f ? l * (1 + s) : l + s - l * s;
//     float p = 2 * l - q;

//     float t[3] = { h + 1.0f/3.0f, h, h - 1.0f/3.0f };
//     float c[3];
//     for (int i = 0; i < 3; ++i) {
//         if (t[i] < 0) t[i] += 1;
//         if (t[i] > 1) t[i] -= 1;
//         if (t[i] < 1.0f/6.0f)
//             c[i] = p + (q - p) * 6 * t[i];
//         else if (t[i] < 1.0f/2.0f)
//             c[i] = q;
//         else if (t[i] < 2.0f/3.0f)
//             c[i] = p + (q - p) * (2.0f/3.0f - t[i]) * 6;
//         else
//             c[i] = p;
//     }

//     *r = c[0];
//     *g = c[1];
//     *b = c[2];
// }





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


// float clamp(float val, float min_val, float max_val) {
//     return fmaxf(min_val, fminf(max_val, val));
// }

void apply_all_adjustments( 
    uint8_t* img, int width, int height,
    float brightness, float contrast, float saturation,
    float shadow_factor, float highlight_factor,
    float temperature, float tint,
    float hsl_h[6], float hsl_s[6], float hsl_l[6]
) {
    int size = width * height * 3;

    for (int i = 0; i < size; i += 3) {
        // float r = img[i + 2] / 255.0f;
        // float g = img[i + 1] / 255.0f;
        // float b = img[i + 0] / 255.0f;

        // // === Brightness ===
        // r = clamp(r + brightness / 255.0f, 0.0f, 1.0f);
        // g = clamp(g + brightness / 255.0f, 0.0f, 1.0f);
        // b = clamp(b + brightness / 255.0f, 0.0f, 1.0f);

        // // === Shadows / Highlights ===
        // float lum = 0.2126f * r + 0.7152f * g + 0.0722f * b;
        // float shadow_or_highlight = lum < 0.5f ? shadow_factor : highlight_factor;
        // r = clamp(r * shadow_or_highlight, 0.0f, 1.0f);
        // g = clamp(g * shadow_or_highlight, 0.0f, 1.0f);
        // b = clamp(b * shadow_or_highlight, 0.0f, 1.0f);

        // // === White balance ===
        // r = clamp(r + temperature / 255.0f, 0.0f, 1.0f);
        // g = clamp(g + tint / 255.0f, 0.0f, 1.0f);
        // b = clamp(b - temperature / 255.0f, 0.0f, 1.0f);

        // // === Contrast ===
        // r = clamp((r - 0.5f) * contrast + 0.5f, 0.0f, 1.0f);
        // g = clamp((g - 0.5f) * contrast + 0.5f, 0.0f, 1.0f);
        // b = clamp((b - 0.5f) * contrast + 0.5f, 0.0f, 1.0f);

        // // === RGB → HSL ===
        // float h, s, l;
        // rgb_to_hsl(r, g, b, &h, &s, &l);

        // // Banded HSL adjustments
        // // int band = (int)(h * 6.0f);
        // // if (band < 0) band = 0;
        // // if (band > 5) band = 5;

        // int band = (int)(h * 6.0f);
        // band = band % 6;
        // if (band < 0) band += 6;


        // h += hsl_h[band];
        // if (h > 1.0f) h -= 1.0f;
        // if (h < 0.0f) h += 1.0f;

        // s = clamp(s * saturation * hsl_s[band], 0.0f, 1.0f);
        // l = clamp(l * hsl_l[band], 0.0f, 1.0f);

        // // === HSL → RGB ===
        // float q = l < 0.5f ? l * (1 + s) : (l + s - l * s);
        // float p = 2 * l - q;
        // float t[3] = { h + 1.0f / 3.0f, h, h - 1.0f / 3.0f };
        // float c[3];
        // for (int j = 0; j < 3; ++j) {
        //     if (t[j] < 0) t[j] += 1;
        //     if (t[j] > 1) t[j] -= 1;
        //     if (t[j] < 1.0f / 6.0f)
        //         c[j] = p + (q - p) * 6.0f * t[j];
        //     else if (t[j] < 0.5f)
        //         c[j] = q;
        //     else if (t[j] < 2.0f / 3.0f)
        //         c[j] = p + (q - p) * (2.0f / 3.0f - t[j]) * 6.0f;
        //     else
        //         c[j] = p;
        // }

        // r = clamp(c[0] * 255.0f, 0.0f, 255.0f);
        // g = clamp(c[1] * 255.0f, 0.0f, 255.0f);
        // b = clamp(c[2] * 255.0f, 0.0f, 255.0f);

        // img[i + 2] = (uint8_t)r;
        // img[i + 1] = (uint8_t)g;
        // img[i + 0] = (uint8_t)b;


        float r = img[i + 2] / 255.0f;
        float g = img[i + 1] / 255.0f;
        float b = img[i + 0] / 255.0f;

        // ---- Step 1: Apply brightness/contrast/etc. ----

        // Brightness
        r += brightness / 255.0f;
        g += brightness / 255.0f;
        b += brightness / 255.0f;

        // Shadows / Highlights
        float lum = 0.2126f * r + 0.7152f * g + 0.0722f * b;
        float factor = lum < 0.5f ? shadow_factor : highlight_factor;
        r *= factor;
        g *= factor;
        b *= factor;

        // White balance
        r += temperature / 255.0f;
        g += tint / 255.0f;
        b -= temperature / 255.0f;

        // Contrast
        r = (r - 0.5f) * contrast + 0.5f;
        g = (g - 0.5f) * contrast + 0.5f;
        b = (b - 0.5f) * contrast + 0.5f;

        // Clamp after all
        r = clamp(r, 0.0f, 1.0f);
        g = clamp(g, 0.0f, 1.0f);
        b = clamp(b, 0.0f, 1.0f);

        // ---- Step 2: HSL adjustment ----

        float h, s, l;
        rgb_to_hsl(r, g, b, &h, &s, &l);

        int band = (int)(h * 6.0f) % 6;
        if (band < 0) band += 6;

        h += hsl_h[band];
        if (h > 1.0f) h -= 1.0f;
        if (h < 0.0f) h += 1.0f;

        s = clamp(s * hsl_s[band], 0.0f, 1.0f);
        l = clamp(l * hsl_l[band], 0.0f, 1.0f);

        // ---- Step 3: Convert back to RGB ----

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

        img[i + 2] = (uint8_t)(r * 255.0f);
        img[i + 1] = (uint8_t)(g * 255.0f);
        img[i + 0] = (uint8_t)(b * 255.0f);


    }
}

