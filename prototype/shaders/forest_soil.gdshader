shader_type spatial;
uniform vec4 peat_dark : source_color = vec4(0.26, 0.23, 0.19, 1.0);
uniform vec4 peat_light : source_color = vec4(0.40, 0.36, 0.28, 1.0);
varying vec3 world_position;

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    vec4 h = fract(sin(vec4(dot(i, vec2(127.1, 311.7)), dot(i + vec2(1, 0), vec2(127.1, 311.7)),
                              dot(i + vec2(0, 1), vec2(127.1, 311.7)), dot(i + 1.0, vec2(127.1, 311.7)))) * 43758.5453);
    return mix(mix(h.x, h.y, f.x), mix(h.z, h.w, f.x), f.y);
}

void vertex() {
    world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
    vec2 p = world_position.xz;
    float broad = noise(p * 0.8) * 0.6 + noise(p * 3.6) * 0.3 + noise(p * 16.0) * 0.1;
    float width = 0.66 + clamp(p.y, 0.0, 16.0) * 0.035;
    float path = (1.0 - smoothstep(width, width + 0.65, abs(p.x - sin(p.y * 0.42) * 0.24) + broad * 0.4)) * smoothstep(-2.0, 0.0, p.y);
    ALBEDO = mix(peat_dark.rgb, peat_light.rgb, broad * 0.8 + path * 0.2);
    ROUGHNESS = 0.94;
    SPECULAR = 0.08;
}
