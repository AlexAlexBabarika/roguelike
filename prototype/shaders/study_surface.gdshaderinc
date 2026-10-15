uniform vec4 pigment : source_color = vec4(0.3, 0.35, 0.3, 1.0);
uniform bool gouache = false;
uniform bool foliage = false;
uniform bool actor = false;
uniform bool roof = false;
uniform bool atmosphere = false;
uniform bool raining = true;
uniform bool pigment_debug = false;
uniform bool wind_enabled = true;
uniform float clock = 6.0;
uniform vec3 focus = vec3(-0.5, 0.0, 4.45);
varying vec3 rest_position;
varying float light_sheen;

void vertex() {
    rest_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
    if (foliage && wind_enabled) {
        float bend = smoothstep(1.3, 7.0, rest_position.y);
        VERTEX.x += sin(clock * 0.8 + rest_position.z * 0.7 + rest_position.x * 0.4) * 0.065 * bend;
        VERTEX.z += cos(clock * 0.7 + rest_position.x * 0.6) * 0.035 * bend;
    }
}

void fragment() {
    float pooling = actor ? 0.0 : COLOR.r;
    float wet = (raining && !actor) ? COLOR.g : 0.0;
    float patch = sin(rest_position.x * 1.2566 + rest_position.y * 1.0472) * sin(rest_position.z * 1.0472);
    ALBEDO = pigment.rgb * (1.0 - pooling * (gouache ? 0.12 : 0.22));
    if (gouache && !actor) {
        ALBEDO *= 1.0 + patch * 0.06;
        ALBEDO *= 1.0 - wet * 0.18;
        ALBEDO += vec3(-0.004, 0.0, 0.006) * pooling;
    }
    ROUGHNESS = gouache ? mix(0.95, 0.55, wet) : 0.75;
    SPECULAR = gouache ? wet * 0.25 : 0.3;
    light_sheen = SPECULAR;
    if (actor) {
        float rim = pow(1.0 - max(dot(NORMAL, VIEW), 0.0), 3.0);
        EMISSION = pigment.rgb * rim * 0.18;
    }
    if (atmosphere && !actor) {
        float distance_from_focus = length(rest_position.xz - focus.xz);
        float haze = smoothstep(12.0, 28.0, distance_from_focus) * 0.34;
        ALBEDO = mix(ALBEDO, vec3(0.22, 0.30, 0.32), haze);
        EMISSION += vec3(0.16, 0.22, 0.24) * haze;
        if (foliage) { ALBEDO *= mix(0.84, 1.0, COLOR.g); }
        if (roof) { ALBEDO *= mix(0.78, 1.02, smoothstep(3.0, 6.4, rest_position.y)); }
    }
    if (pigment_debug && !actor) {
        ALBEDO = vec3(0.0);
        EMISSION = vec3(0.45 + patch * 0.3);
    }
}
