shader_type spatial;
render_mode cull_disabled;

uniform vec4 pigment : source_color = vec4(0.2, 0.3, 0.2, 1.0);
uniform float clock = 6.0;
uniform bool wind_enabled = true;
varying vec3 world_position;

void vertex() {
    vec3 p = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
    float bend = smoothstep(1.3, 7.0, p.y);
    if (wind_enabled) {
        VERTEX.x += sin(clock * 0.8 + p.z * 0.7 + p.x * 0.4) * 0.065 * bend;
        VERTEX.z += cos(clock * 0.7 + p.x * 0.6) * 0.035 * bend;
    }
    world_position = p;
}

void fragment() {
    float patch = sin(world_position.x * 5.0 + world_position.y * 2.0) * sin(world_position.z * 4.0);
    ALBEDO = pigment.rgb * (0.96 + patch * 0.045);
    ROUGHNESS = 0.94;
}
