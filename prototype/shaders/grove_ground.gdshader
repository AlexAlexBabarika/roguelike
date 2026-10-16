shader_type spatial;

uniform sampler2D litter : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D litter_normal : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D moss : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D moss_normal : hint_normal, filter_linear_mipmap, repeat_enable;
varying vec3 world;

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    vec4 h = fract(sin(vec4(dot(i, vec2(127.1, 311.7)), dot(i + vec2(1, 0), vec2(127.1, 311.7)),
                              dot(i + vec2(0, 1), vec2(127.1, 311.7)), dot(i + 1.0, vec2(127.1, 311.7)))) * 43758.5453);
    return mix(mix(h.x, h.y, f.x), mix(h.z, h.w, f.x), f.y);
}

void vertex() {
    world = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
    vec2 p = world.xz;
    float n = noise(p * 0.45) * 0.7 + noise(p * 1.6) * 0.3;
    float edge = abs(p.x + 0.55 - sin(p.y * 0.3) * 0.9);
    float path = (1.0 - smoothstep(0.9, 2.3, edge + n * 0.6)) * smoothstep(-1.8, 0.3, p.y);
    float vegetation = smoothstep(0.28, 0.72, n) * (1.0 - path);
    vec3 earth = texture(litter, p * 0.24).rgb;
    vec3 green = texture(moss, p * 0.31).rgb;
    vec3 base = mix(earth * vec3(0.73, 0.79, 0.72), green * vec3(0.68, 0.78, 0.60), vegetation * 0.85);
    base = mix(base, earth * vec3(0.86, 0.83, 0.73), path * 0.6);
    ALBEDO = base * mix(0.78, 1.05, n);
    NORMAL_MAP = normalize(mix(texture(litter_normal, p * 0.24).rgb * 2.0 - 1.0,
                               texture(moss_normal, p * 0.31).rgb * 2.0 - 1.0, vegetation)) * 0.5 + 0.5;
    NORMAL_MAP_DEPTH = 0.7;
    ROUGHNESS = 0.95;
    SPECULAR = 0.05;
}
