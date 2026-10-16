shader_type spatial;
render_mode cull_disabled, specular_disabled;

uniform vec4 pigment : source_color = vec4(0.25, 0.35, 0.32, 1.0);
uniform bool roof = false;
uniform bool foliage = false;
uniform bool raining = true;
uniform bool wind_enabled = true;
uniform float clock = 6.0;
varying vec3 rest_position;

void vertex() {
    rest_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
    if (foliage && wind_enabled) {
        float bend = smoothstep(1.3, 7.0, rest_position.y);
        VERTEX.x += sin(clock * 0.8 + rest_position.z * 0.7 + rest_position.x * 0.4) * 0.065 * bend;
    }
}

void fragment() {
    float broad = sin(rest_position.x * 1.3 + rest_position.z * 0.45)
                * cos(rest_position.y * 1.5 - rest_position.z * 1.1);
    float wash = smoothstep(-0.25, 0.48, broad);
    vec3 ink = pigment.rgb;
    if (roof) {
        float strokes = sin(rest_position.x * 7.0 + rest_position.z * 2.8 + broad * 2.0);
        ink = mix(vec3(0.075, 0.13, 0.17), vec3(0.23, 0.32, 0.33), wash);
        ink *= mix(0.85, 1.09, smoothstep(-0.25, 0.85, strokes));
    } else if (foliage) {
        ink = mix(vec3(0.07, 0.12, 0.12), pigment.rgb * 1.14, wash);
    } else {
        ink = mix(pigment.rgb * 0.63, pigment.rgb * 1.13, wash);
    }
    ink *= 1.0 - COLOR.r * 0.18;
    if (raining) {
        ink *= 1.0 - COLOR.g * 0.06;
    }
    ALBEDO = ink;
    ROUGHNESS = 0.96;
    SPECULAR = 0.0;
}

void light() {
    float lambert = dot(NORMAL, LIGHT);
    float wrapped = smoothstep(-0.38, 0.60, lambert);
    DIFFUSE_LIGHT += mix(0.44, 0.88, wrapped) * LIGHT_COLOR * ATTENUATION / PI;
}
