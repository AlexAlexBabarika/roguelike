shader_type spatial;
render_mode cull_disabled, diffuse_lambert, specular_disabled;

uniform sampler2D branches : source_color, filter_linear_mipmap, repeat_disable;
uniform bool silhouette = false;
uniform bool wind_enabled = true;
uniform float clock = 6.0;
varying vec3 rest;

void vertex() {
    rest = VERTEX;
    NORMAL = normalize(vec3(VERTEX.x * 0.22, 0.9, VERTEX.z * 0.22));
    if (wind_enabled) {
        VERTEX.x += sin(clock * 0.9 + VERTEX.y * 1.6) * 0.012 * max(VERTEX.y - 1.5, 0.0);
    }
}

void fragment() {
    vec4 leaf = texture(branches, UV);
    ALPHA = leaf.a;
    ALPHA_SCISSOR_THRESHOLD = 0.24;
    float crown = smoothstep(1.4, 8.0, rest.y);
    ALBEDO = silhouette ? vec3(0.006) : leaf.rgb * mix(0.72, 1.12, crown);
    ROUGHNESS = 0.92;
    SPECULAR = 0.0;
}
