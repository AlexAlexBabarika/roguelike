shader_type spatial;
render_mode unshaded, cull_disabled;

uniform sampler2D reflection_texture : filter_linear, repeat_disable;
uniform mat4 reflection_view;
uniform mat4 reflection_projection;
uniform float clock = 6.0;
uniform bool reflections_enabled = true;
varying vec3 world_position;

void vertex() {
    world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
    vec4 projected = reflection_projection * reflection_view * vec4(world_position, 1.0);
    vec2 uv = projected.xy / projected.w * 0.5 + 0.5;
    uv.y = 1.0 - uv.y;
    vec2 p = world_position.xz;
    uv += vec2(sin(p.y * 9.0 + clock), cos(p.x * 7.0 - clock)) * 0.0012;
    vec3 reflection = texture(reflection_texture, clamp(uv, vec2(0.001), vec2(0.999))).rgb;
    float ring = 0.0;
    for (int i = 0; i < 4; i++) {
        vec2 cell = floor(p * 0.8) + vec2(float(i) * 0.13);
        vec2 center = cell / 0.8 + vec2(sin(cell.x * 12.7 + float(i)), cos(cell.y * 19.1 + float(i))) * 0.25;
        float age = fract(clock * 0.55 + sin(dot(cell, vec2(12.9, 78.2)) + float(i)) * 12.1);
        float distance = length(p - center);
        ring += (1.0 - smoothstep(0.009, 0.035, abs(distance - age * 0.42))) * (1.0 - age) * 0.025;
    }
    vec3 base = vec3(0.055, 0.085, 0.085);
    ALBEDO = reflections_enabled ? mix(base, reflection, 0.48) : base;
    ALBEDO += vec3(0.55, 0.65, 0.60) * ring;
}
