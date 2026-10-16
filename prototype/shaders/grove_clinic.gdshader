shader_type spatial;

uniform sampler2D wood : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D metal : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D stone : source_color, filter_linear_mipmap, repeat_enable;
uniform vec4 base_color : source_color = vec4(0.4, 0.42, 0.36, 1.0);
uniform int surface_kind = 0;
varying vec3 world;
varying vec3 axis;

void vertex() {
    world = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
    axis = abs(MODEL_NORMAL_MATRIX * NORMAL);
}

void fragment() {
    vec3 weights = pow(axis, vec3(6.0));
    weights /= max(dot(weights, vec3(1.0)), 0.001);
    vec2 front = vec2(world.x * 0.38, world.y * 0.38);
    vec2 side = vec2(world.z * 0.38, world.y * 0.38);
    vec3 grain = texture(wood, front).rgb * weights.z + texture(wood, side).rgb * weights.x
                   + texture(wood, world.xz * 0.38).rgb * weights.y;
    float streak = texture(wood, vec2(world.x + world.z, world.y * 0.12)).r;
    float damp = 1.0 - smoothstep(0.1, 1.4, world.y + streak * 0.6);
    vec3 shade = base_color.rgb;
    if (surface_kind == 0) {
        shade *= mix(vec3(0.55, 0.65, 0.50), vec3(1.0), 1.0 - damp * 0.65);
        shade *= 0.72 + 0.65 * grain;
    } else if (surface_kind == 1) {
        shade = grain * vec3(0.78, 0.87, 0.79);
    } else if (surface_kind == 2) {
        vec3 rust = texture(metal, world.xz * 0.20).rgb;
        shade = mix(base_color.rgb, rust * 0.65, 0.34);
        shade *= 0.75 + texture(wood, world.xz * 0.1).r * 0.55;
    } else {
        shade = (texture(stone, world.xy * 0.6).rgb * weights.z
                   + texture(stone, world.zy * 0.6).rgb * weights.x
                   + texture(stone, world.xz * 0.6).rgb * weights.y) * vec3(0.77, 0.83, 0.75);
    }
    ALBEDO = shade;
    ROUGHNESS = 0.92;
    SPECULAR = 0.12;
}
