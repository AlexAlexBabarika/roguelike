shader_type spatial;
render_mode cull_disabled, unshaded, depth_prepass_alpha;

uniform sampler2D atlas : source_color, filter_linear_mipmap, repeat_disable;
uniform float clock = 6.0;
uniform bool wind_enabled = true;
varying vec4 card_data;

void vertex() {
    card_data = INSTANCE_CUSTOM;
    vec3 scale = vec3(length(MODEL_MATRIX[0].xyz), length(MODEL_MATRIX[1].xyz), length(MODEL_MATRIX[2].xyz));
    vec3 facing = normalize(vec3(INV_VIEW_MATRIX[2].x, 0.0, INV_VIEW_MATRIX[2].z));
    vec3 right = normalize(cross(vec3(0.0, 1.0, 0.0), facing));
    MODELVIEW_MATRIX = VIEW_MATRIX * mat4(vec4(right * scale.x, 0.0), vec4(0.0, scale.y, 0.0, 0.0),
                                        vec4(facing * scale.z, 0.0), MODEL_MATRIX[3]);
    if (wind_enabled) {
        VERTEX.x += sin(clock * 0.75 + card_data.b * TAU) * (0.025 + UV.y * 0.03);
    }
}

void fragment() {
    vec2 stamp_uv = UV * 0.5 + card_data.rg * 0.5;
    vec4 color = texture(atlas, stamp_uv);
    ALBEDO = color.rgb * mix(0.86, 1.05, card_data.a);
    ALPHA = color.a;
    ALPHA_SCISSOR_THRESHOLD = 0.36;
}
