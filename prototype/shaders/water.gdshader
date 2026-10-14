shader_type spatial;
render_mode unshaded, cull_disabled;

uniform sampler2D reflection_texture : filter_linear, repeat_disable;
uniform mat4 reflection_view;
uniform mat4 reflection_projection;
uniform bool reflections_enabled = true;
uniform float rain_amount = 1.0;
uniform vec2 ripple_origin = vec2(0.0);
uniform float ripple_age = 10.0;
varying vec3 world_position;

void vertex() {
    world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
    vec4 projected = reflection_projection * reflection_view * vec4(world_position, 1.0);
    vec2 uv = projected.xy / projected.w * 0.5 + 0.5;
    uv.y = 1.0 - uv.y;
    vec2 p = world_position.xz;
    vec2 waves = vec2(sin(p.y * 6.0 + TIME * 2.2), cos(p.x * 5.0 - TIME * 1.5));
    float distance_to_step = length(p - ripple_origin);
    float ring = sin(distance_to_step * 15.0 - ripple_age * 14.0) * exp(-abs(distance_to_step - ripple_age * 1.8) * 3.5) * exp(-ripple_age * 1.0);
    uv += waves * 0.0035 + ring * 0.008;
    vec3 reflected = texture(reflection_texture, clamp(uv, vec2(0.001), vec2(0.999))).rgb;
    vec3 dark_water = vec3(0.025, 0.06, 0.085);
    float small_ripples = pow(max(0.0, sin(p.x * 32.0 + TIME * 5.0) * sin(p.y * 35.0 - TIME * 4.0)), 18.0) * rain_amount;
    ALBEDO = reflections_enabled ? mix(dark_water, reflected, 0.82) : dark_water;
    ALBEDO += vec3(0.045, 0.065, 0.08) * (small_ripples + max(ring, 0.0));
}
