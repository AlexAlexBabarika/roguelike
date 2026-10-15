shader_type spatial;

uniform bool mud = false;
uniform vec4 peat_dark : source_color = vec4(0.25, 0.28, 0.22, 1.0);
uniform vec4 peat_light : source_color = vec4(0.34, 0.36, 0.27, 1.0);
uniform vec4 earth_dark : source_color = vec4(0.31, 0.29, 0.25, 1.0);
uniform vec4 earth_light : source_color = vec4(0.39, 0.35, 0.28, 1.0);
varying vec3 world_position;

float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float noise(vec2 p) {
    vec2 cell = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash(cell), hash(cell + vec2(1.0, 0.0)), f.x),
               mix(hash(cell + vec2(0.0, 1.0)), hash(cell + vec2(1.0)), f.x), f.y);
}

void vertex() {
    world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
    vec2 p = world_position.xz;
    float broad = noise(p * 0.42);
    float fine = noise(p * 8.0);
    vec3 peat = mix(peat_dark.rgb, peat_light.rgb, broad);
    vec3 earth = mix(earth_dark.rgb, earth_light.rgb, broad);
    ALBEDO = (mud ? earth : peat) * (0.95 + fine * 0.1);
    ROUGHNESS = mud ? mix(0.56, 0.79, broad) : 0.95;
    SPECULAR = mud ? 0.2 : 0.08;
}
