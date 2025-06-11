// adjustments.c
#include <stdint.h>
#include <math.h>
#include <stdlib.h>
#include <math.h>


// float clamp(float val, float min_val, float max_val) {
//     return fmaxf(min_val, fminf(max_val, val));
// }


// // Helper to convert BGR to HSL (simplified, not 100% accurate for speed)
// void rgb_to_hsl(float r, float g, float b, float *h, float *s, float *l) {
//     float max = fmaxf(fmaxf(r, g), b);
//     float min = fminf(fminf(r, g), b);
//     float d = max - min;

//     *l = (max + min) / 2.0f;

//     if (d == 0.0f) {
//         *h = *s = 0.0f;
//     } else {
//         *s = (*l > 0.5f) ? d / (2.0f - max - min) : d / (max + min);

//         if (max == r)
//             *h = (g - b) / d + (g < b ? 6 : 0);
//         else if (max == g)
//             *h = (b - r) / d + 2;
//         else
//             *h = (r - g) / d + 4;

//         *h /= 6.0f;
//     }
// }



// // Reapply HSL adjustments with limited logic
// void apply_hsl_mod(float *r, float *g, float *b,
//                    float *hue_adj, float *sat_adj, float *lum_adj) {
//     float h, s, l;
//     rgb_to_hsl(*r, *g, *b, &h, &s, &l);

//     // Example: apply global sat/lum scaling
//     s = clamp(s * sat_adj[0], 0.0f, 1.0f);
//     l = clamp(l * lum_adj[0], 0.0f, 1.0f);

//     // Convert HSL back to RGB (simplified, or you can use LUTs)
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



// Clamp helper
float clamp(float val, float min_val, float max_val) {
    return fminf(fmaxf(val, min_val), max_val);
}

// Improved band matching by hue distance
int get_band(float h_deg) {
    float hue_centers[] = {0, 30, 60, 120, 180, 240, 270, 300}; // Red to Magenta
    int band = 0;
    float min_dist = 360.0f;

    for (int i = 0; i < 8; i++) {
        float dist = fabsf(h_deg - hue_centers[i]);
        if (dist > 180.0f) dist = 360.0f - dist;
        if (dist < min_dist) {
            min_dist = dist;
            band = i;
        }
    }
    return band;
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

float hue_to_rgb(float p, float q, float t) {
    if (t < 0.0f) t += 1.0f;
    if (t > 1.0f) t -= 1.0f;
    if (t < 1.0f/6.0f) return p + (q - p) * 6.0f * t;
    if (t < 1.0f/2.0f) return q;
    if (t < 2.0f/3.0f) return p + (q - p) * (2.0f/3.0f - t) * 6.0f;
    return p;
}

void hsl_to_rgb(float h, float s, float l, float *r, float *g, float *b) {
    if (s == 0.0f) {
        *r = *g = *b = l;
    } else {
        float q = l < 0.5f ? (l * (1.0f + s)) : (l + s - l * s);
        float p = 2.0f * l - q;
        *r = hue_to_rgb(p, q, h + 1.0f/3.0f);
        *g = hue_to_rgb(p, q, h);
        *b = hue_to_rgb(p, q, h - 1.0f/3.0f);
    }
}


#define NUM_BANDS 8
const float hue_centers[NUM_BANDS] = {0, 30, 60, 120, 180, 240, 270, 300}; // Red to Magenta

float hue_distance(float a, float b) {
    float d = fabsf(a - b);
    return fminf(d, 360.0f - d);  // Circular distance
}

float weight_for_band(float h_deg, float center_deg, float falloff_deg) {
    float d = hue_distance(h_deg, center_deg);
    return expf(- (d * d) / (2.0f * falloff_deg * falloff_deg));
}

void apply_hsl_mod(unsigned char* img, int width, int height, int channels,
                   float* hue_adj, float* sat_adj, float* lum_adj) {

    float falloff_deg = 30.0f;  // You can tune this (20–40 gives smooth results)

    for (int i = 0; i < width * height; i++) {
        unsigned char* pixel = &img[i * channels];
        float r = pixel[0] / 255.0f;
        float g = pixel[1] / 255.0f;
        float b = pixel[2] / 255.0f;

        float h, s, l;
        rgb_to_hsl(r, g, b, &h, &s, &l);
        float h_deg = h * 360.0f;

        float h_shift = 0.0f;
        float s_mul = 1.0f;
        float l_mul = 1.0f;
        float total_weight = 0.0f;

        // Smoothly blend adjustments from all bands
        for (int j = 0; j < NUM_BANDS; j++) {
            float weight = weight_for_band(h_deg, hue_centers[j], falloff_deg);
            total_weight += weight;
            h_shift += hue_adj[j] * weight;
            s_mul += (sat_adj[j] - 1.0f) * weight;
            l_mul += (lum_adj[j] - 1.0f) * weight;
        }

        if (total_weight > 0.0f) {
            h += (h_shift / total_weight) / 6.0f;
            s *= clamp(s_mul / total_weight, 0.0f, 10.0f);
            l *= clamp(l_mul / total_weight, 0.0f, 10.0f);
        }

        h = fmodf(h, 1.0f);
        if (h < 0.0f) h += 1.0f;
        s = clamp(s, 0.0f, 1.0f);
        l = clamp(l, 0.0f, 1.0f);

        hsl_to_rgb(h, s, l, &r, &g, &b);
        pixel[0] = (unsigned char)(clamp(r, 0.0f, 1.0f) * 255.0f);
        pixel[1] = (unsigned char)(clamp(g, 0.0f, 1.0f) * 255.0f);
        pixel[2] = (unsigned char)(clamp(b, 0.0f, 1.0f) * 255.0f);
    }
}



// === Main Function ===
// void apply_hsl_mod(unsigned char* img, int width, int height, int channels,
//                    float* hue_adj, float* sat_adj, float* lum_adj) {
//     for (int i = 0; i < width * height; i++) {
//         unsigned char* pixel = &img[i * channels];
//         float r = pixel[0] / 255.0f;
//         float g = pixel[1] / 255.0f;
//         float b = pixel[2] / 255.0f;

//         float h, s, l;
//         rgb_to_hsl(r, g, b, &h, &s, &l);

//         float h_deg = h * 360.0f;
//         int band = get_band(h_deg);

//         // Apply adjustments
//         h += hue_adj[band] / 6.0f;  // map [-2.0, 2.0] to [-1/3, 1/3] cycle
//         h = fmodf(h, 1.0f);
//         if (h < 0.0f) h += 1.0f;

//         s *= sat_adj[band];
//         s = clamp(s, 0.0f, 1.0f);

//         l *= lum_adj[band];
//         l = clamp(l, 0.0f, 1.0f);

//         hsl_to_rgb(h, s, l, &r, &g, &b);

//         pixel[0] = (unsigned char)(clamp(r, 0.0f, 1.0f) * 255.0f);
//         pixel[1] = (unsigned char)(clamp(g, 0.0f, 1.0f) * 255.0f);
//         pixel[2] = (unsigned char)(clamp(b, 0.0f, 1.0f) * 255.0f);
//     }
// }



void apply_all_adjustments( 
    uint8_t* img, int width, int height,
    float brightness, float contrast, float saturation,
    float shadow_factor, float highlight_factor,
    float temperature, float tint,
    float hsl_h[8], float hsl_s[8], float hsl_l[8]
    // float hsl_h[6], float hsl_s[6], float hsl_l[6]
) {
    int size = width * height * 3;

    for (int i = 0; i < size; i += 3) {

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

        // Clamp here before contrast
        r = clamp(r, 0.0f, 1.0f);
        g = clamp(g, 0.0f, 1.0f);
        b = clamp(b, 0.0f, 1.0f);

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

        // int band = (int)(h * 6.0f) % 6;
        int band = (int)(h * 8.0f) % 8;

        if (band < 0) band += 8;

        // h += hsl_h[band] / 6.0f;
        // if (h > 1.0f) h -= 1.0f;
        // if (h < 0.0f) h += 1.0f;

                // Skip hue adjustments on nearly gray or black areas
        if (s > 0.1f && l > 0.05f) {
            h += hsl_h[band] / 6.0f;
            if (h > 1.0f) h -= 1.0f;
            if (h < 0.0f) h += 1.0f;
        }


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

