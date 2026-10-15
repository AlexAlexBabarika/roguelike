shader_type spatial;
render_mode cull_disabled;
#include "study_surface.gdshaderinc"

void light() {
    float wrapped = clamp((dot(NORMAL, LIGHT) + 0.4) / 1.4, 0.0, 1.0);
    float ramp = mix(0.12, 0.55, smoothstep(0.05, 0.55, wrapped));
    ramp = mix(ramp, 1.0, smoothstep(0.45, 1.0, wrapped));
    float shadow = LIGHT_IS_DIRECTIONAL ? mix(0.35, 1.0, ATTENUATION) : ATTENUATION;
    DIFFUSE_LIGHT += ramp * LIGHT_COLOR * shadow / PI;
    float shine = pow(max(dot(NORMAL, normalize(LIGHT + VIEW)), 0.0), 24.0);
    SPECULAR_LIGHT += LIGHT_COLOR * shine * ATTENUATION * light_sheen * 0.12;
}
