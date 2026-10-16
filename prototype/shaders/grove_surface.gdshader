shader_type spatial;
render_mode cull_disabled;

uniform sampler2D color_map : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D normal_map : hint_normal, filter_linear_mipmap, repeat_enable;
uniform vec4 tint : source_color = vec4(1.0);
uniform bool foliage = false;
uniform bool silhouette = false;
uniform bool wind_enabled = true;
uniform float clock = 6.0;
uniform float normal_strength = 0.6;
uniform float map_scale = 1.0;

void vertex() {
    if (foliage && wind_enabled) {
        VERTEX.x += sin(clock * 0.8 + VERTEX.y * 0.9 + VERTEX.z) * 0.015 * max(VERTEX.y - 2.0, 0.0);
    }
}

void fragment() {
    vec4 texel = texture(color_map, UV * map_scale);
    ALBEDO = silhouette ? vec3(0.004) : texel.rgb * tint.rgb;
    NORMAL_MAP = texture(normal_map, UV * map_scale).rgb;
    NORMAL_MAP_DEPTH = normal_strength;
    ROUGHNESS = 0.92;
    SPECULAR = 0.08;
    ALPHA = foliage ? texel.a : 1.0;
    ALPHA_SCISSOR_THRESHOLD = 0.38;
}
