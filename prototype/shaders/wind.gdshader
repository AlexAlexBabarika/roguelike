shader_type spatial;
render_mode cull_disabled;

uniform float wind_strength = 1.0;
uniform vec3 grass_color : source_color = vec3(0.10, 0.36, 0.13);
varying float blade_height;

void vertex() {
    blade_height = UV.y;
    vec3 world = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
    float gust = sin(TIME * 1.8 + world.x * 0.45 + world.z * 0.35);
    float flutter = sin(TIME * 4.0 + world.z * 1.5);
    VERTEX.x += (gust * 0.32 + flutter * 0.055 + 0.17) * UV.y * UV.y * wind_strength;
    VERTEX.z += cos(TIME * 1.6 + world.x * 0.7) * 0.12 * UV.y * UV.y * wind_strength;
}

void fragment() {
    ALBEDO = grass_color * mix(0.45, 1.3, blade_height);
    ROUGHNESS = 0.9;
}
