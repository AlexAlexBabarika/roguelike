shader_type spatial;
render_mode unshaded, cull_disabled, shadows_disabled, depth_draw_never;

uniform float clock = 6.0;
uniform float amount = 1.0;

void vertex() {
    VERTEX.y -= mod(clock * 7.0 + INSTANCE_CUSTOM.x * 11.0, 11.0);
    VERTEX.x -= mod(clock * 7.0 + INSTANCE_CUSTOM.x * 11.0, 11.0) * 0.16;
}

void fragment() {
    ALBEDO = vec3(0.56, 0.68, 0.66);
    ALPHA = 0.19 * amount;
}
