shader_type canvas_item;
render_mode unshaded;

uniform sampler2D scene : hint_screen_texture, filter_linear, repeat_disable;
uniform sampler2D protection : filter_linear, repeat_disable;
uniform float radius_pixels = 5.0;

vec3 region(vec2 uv, vec2 step_size, vec2 quadrant, out float variance) {
    vec3 mean = vec3(0.0);
    vec3 squares = vec3(0.0);
    for (int y = 0; y < 3; y++) {
        for (int x = 0; x < 3; x++) {
            vec3 sample_color = texture(scene, uv + quadrant * step_size * vec2(float(x), float(y)) * 0.5).rgb;
            mean += sample_color / 9.0;
            squares += sample_color * sample_color / 9.0;
        }
    }
    vec3 spread = squares - mean * mean;
    variance = dot(max(spread, vec3(0.0)), vec3(0.2126, 0.7152, 0.0722));
    return mean;
}

void fragment() {
    vec2 radius = SCREEN_PIXEL_SIZE * radius_pixels;
    float guard = texture(protection, SCREEN_UV).r;
    for (int y = -1; y <= 1; y++) {
        for (int x = -1; x <= 1; x++) {
            guard = max(guard, texture(protection, SCREEN_UV + vec2(float(x), float(y)) * radius).r);
        }
    }
    vec3 original = texture(scene, SCREEN_UV).rgb;
    vec3 paint = vec3(0.0);
    float total = 0.0;
    for (int y = -1; y <= 1; y += 2) {
        for (int x = -1; x <= 1; x += 2) {
            float variance;
            vec3 mean = region(SCREEN_UV, radius, vec2(float(x), float(y)), variance);
            float weight = pow(1.0 + variance * 180.0, -5.0);
            paint += mean * weight;
            total += weight;
        }
    }
    COLOR = vec4(mix(paint / total, original, smoothstep(0.05, 0.5, guard)), 1.0);
}
