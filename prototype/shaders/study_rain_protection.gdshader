shader_type spatial;
render_mode unshaded, cull_disabled, fog_disabled;

uniform float clock = 6.0;

void vertex() {
    VERTEX.y -= mod(clock * 7.0 + INSTANCE_CUSTOM.x * 11.0, 11.0);
    VERTEX.x -= mod(clock * 7.0 + INSTANCE_CUSTOM.x * 11.0, 11.0) * 0.16;
}

void fragment() {
    ALBEDO = vec3(1.0);
}
