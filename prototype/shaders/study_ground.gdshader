shader_type spatial;
uniform bool mud = false;
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
    // Test 2 intentionally changes the floor value, not the scene lights.
    vec3 peat = mix(vec3(0.42, 0.44, 0.36), vec3(0.53, 0.53, 0.43), broad);
    vec3 earth = mix(vec3(0.44, 0.41, 0.35), vec3(0.55, 0.50, 0.41), broad);
    ALBEDO = (mud ? earth : peat) * (0.97 + fine * 0.06);
    float haze = smoothstep(12.0, 28.0, length(p - vec2(-0.5, 4.45))) * 0.34;
    ALBEDO = mix(ALBEDO, vec3(0.22, 0.30, 0.32), haze);
    EMISSION = vec3(0.16, 0.22, 0.24) * haze;
    ROUGHNESS = mud ? mix(0.56, 0.79, broad) : 0.95;
    SPECULAR = mud ? 0.2 : 0.08;
}
