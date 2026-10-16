shader_type spatial;

uniform sampler2D terrain_color : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D terrain_normal : hint_normal, filter_linear_mipmap, repeat_enable;
uniform float detail_strength : hint_range(0.0, 1.0) = 1.0;
varying vec2 terrain_uv;

void vertex() {
    terrain_uv = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xz / 64.0 + 0.5;
}

void fragment() {
    ALBEDO = mix(vec3(0.15, 0.17, 0.12), texture(terrain_color, terrain_uv).rgb, detail_strength);
    NORMAL_MAP = texture(terrain_normal, terrain_uv).rgb;
    NORMAL_MAP_DEPTH = 0.5 * detail_strength;
    ROUGHNESS = 0.95;
    SPECULAR = 0.05;
}
