shader_type spatial;
render_mode unshaded, cull_disabled, shadows_disabled;

uniform float wind_strength = 1.0;
uniform float rain_amount = 1.0;

void vertex() {
    float seed = INSTANCE_CUSTOM.x;
    float drop = mod(INSTANCE_CUSTOM.y * 14.0 - TIME * (9.0 + seed * 3.0), 14.0);
    VERTEX.y += drop;
    VERTEX.x += sin(TIME * 0.9 + seed * 20.0) * 0.6 * wind_strength + drop * 0.14 * wind_strength;
}

void fragment() {
    ALBEDO = vec3(0.34, 0.44, 0.53) * rain_amount;
}
