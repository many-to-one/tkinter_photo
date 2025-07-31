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


float hue_distance(float a, float b) {
    float d = fabsf(a - b);
    return fminf(d, 360.0f - d);  // wrap-around
}

// Gaussian weight
float weight(float distance, float sigma) {
    return expf(-0.5f * (distance / sigma) * (distance / sigma));
}



void apply_primary_adjustment(float* r, float* g, float* b,
                              float hue_r, float sat_r,
                              float hue_g, float sat_g,
                              float hue_b, float sat_b) {
    float rf = *r, gf = *g, bf = *b;
    float h, s, l;
    rgb_to_hsl(rf, gf, bf, &h, &s, &l);

    float hue_deg = h * 360.0f;

    // Parametry środka kolorów
    float center_r = 0.0f;
    float center_g = 120.0f;
    float center_b = 240.0f;
    float sigma = 50.0f;

    // Odległości
    float d_r = hue_distance(hue_deg, center_r);
    float d_g = hue_distance(hue_deg, center_g);
    float d_b = hue_distance(hue_deg, center_b);

    // Wagi Gaussian
    float w_r = weight(d_r, sigma);
    float w_g = weight(d_g, sigma);
    float w_b = weight(d_b, sigma);

    // Hue shift (w Lightroom: +/- 100 → ok. +/- 30 stopni)
    float shift_r = hue_r * 30.0f * w_r;
    float shift_g = hue_g * 30.0f * w_g;
    float shift_b = hue_b * 30.0f * w_b;

    float hue_shift = shift_r + shift_g + shift_b;

    hue_deg += hue_shift;

    if (hue_deg < 0.0f) hue_deg += 360.0f;
    if (hue_deg >= 360.0f) hue_deg -= 360.0f;

    h = hue_deg / 360.0f;

    // Saturation scaling
    float sat_scale =
        powf(sat_r, w_r) *
        powf(sat_g, w_g) *
        powf(sat_b, w_b);

    s *= sat_scale;
    s = clamp(s, 0.0f, 1.0f);

    hsl_to_rgb(h, s, l, &rf, &gf, &bf);

    *r = rf;
    *g = gf;
    *b = bf;
}



// For each hue band (0..7), apply a smooth contribution to the hue
// float soft_hue_shift(float h, float* hsl_h, float sigma) {
//     float new_h = 0.0f;
//     float total_weight = 0.0f;

//     for (int i = 0; i < 8; ++i) {
//         float band_center = (i + 0.5f) / 8.0f;  // center of each band
//         float dist = fabsf(h - band_center);
//         if (dist > 0.5f) dist = 1.0f - dist; // wrap-around hue

//         float weight = expf(-0.5f * (dist / sigma) * (dist / sigma));
//         float shifted = h + hsl_h[i];  // shift hue by hsl_h[i]
//         if (shifted < 0.0f) shifted += 1.0f;
//         if (shifted > 1.0f) shifted -= 1.0f;

//         new_h += shifted * weight;
//         total_weight += weight;
//     }

//     return fmodf(new_h / total_weight, 1.0f);
// }



float soft_hue_shift(float h, float* hsl_h) {
    float shifted_hue = h;
    float sum = 0.0f;
    float total_weight = 0.0f;

    for (int i = 0; i < 8; ++i) {
        // Center of each band in hue space (0.0 to 1.0)
        float center = (i + 0.5f) / 8.0f;

        // Calculate hue distance with wrap-around
        float dist = fabsf(h - center);
        if (dist > 0.5f) dist = 1.0f - dist;

        // Apply Gaussian-like falloff (smooth)
        float weight = expf(-dist * dist * 4.0f);  // smoothness control
        float delta_h = hsl_h[i] / 8.0f;            // scale shift

        sum += delta_h * weight;
        total_weight += weight;
    }

    if (total_weight > 0.0f)
        shifted_hue = h + sum / total_weight;

    // Wrap hue to [0, 1]
    if (shifted_hue < 0.0f) shifted_hue += 1.0f;
    if (shifted_hue > 1.0f) shifted_hue -= 1.0f;

    return shifted_hue;
}


float soft_luminance_shift(float h, float l, float* hsl_l, float sigma) {
    float result = 0.0f;
    float total_weight = 0.0f;

    for (int i = 0; i < 8; ++i) {
        float band_center = (i + 0.5f) / 8.0f;
        float distance = fabsf(h - band_center);
        if (distance > 0.5f) distance = 1.0f - distance; // hue wrap-around
        float w = expf(-0.5f * (distance / sigma) * (distance / sigma)); // Gaussian
        result += l * hsl_l[i] * w;
        total_weight += w;
    }

    return clamp(result / total_weight, 0.0f, 1.0f);
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

        // if (s > 0.1f && l > 0.05f) {
        //     h += hsl_h[band] / 8.0f;
        //     if (h > 1.0f) h -= 1.0f;
        //     if (h < 0.0f) h += 1.0f;
        // }
        if (s > 0.1f && l > 0.05f) {
            h = soft_hue_shift(h, hsl_h);
            // h = soft_hue_shift(h, hsl_h, 0.08f); // <- soften transitions
        }


        s = clamp(s * hsl_s[band], 0.0f, 1.0f);
        // l = clamp(l * hsl_l[band], 0.0f, 1.0f);
        l = soft_luminance_shift(h, l, hsl_l, 0.15f); // 0.08 = softness


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
        // // NOTE: Hue shifts implemented as small channel offsets
        // float r_shift = red_hue * (g - b);
        // float g_shift = green_hue * (b - r);
        // float b_shift = blue_hue * (r - g);

        // r += r_shift;
        // g += g_shift;
        // b += b_shift;

        // // Saturation per primary
        // r = 0.5f + (r - 0.5f) * red_sat;
        // g = 0.5f + (g - 0.5f) * green_sat;
        // b = 0.5f + (b - 0.5f) * blue_sat;

        // r = clamp(r, 0.0f, 1.0f);
        // g = clamp(g, 0.0f, 1.0f);
        // b = clamp(b, 0.0f, 1.0f);

        apply_primary_adjustment(
            &r, &g, &b,
            red_hue, red_sat,
            green_hue, green_sat,
            blue_hue, blue_sat
        );



        // Final safety
        if (!isfinite(r)) r = 0.0f;
        if (!isfinite(g)) g = 0.0f;
        if (!isfinite(b)) b = 0.0f;

        img[i + 2] = (uint8_t)(r * 255.0f);
        img[i + 1] = (uint8_t)(g * 255.0f);
        img[i + 0] = (uint8_t)(b * 255.0f);
    }
}




