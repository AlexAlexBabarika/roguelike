shader_type spatial;
uniform bool silhouette = false;
varying vec3 rest;

void vertex() {
    rest = VERTEX;
}

void fragment() {
    float fissure = pow(abs(sin(rest.x * 105.0 + sin(rest.y * 11.0) * 0.7 + rest.z * 43.0)), 8.0);
    ALBEDO = silhouette ? vec3(0.006) : mix(vec3(0.12, 0.095, 0.073), vec3(0.23, 0.19, 0.14), fissure);
    ROUGHNESS = 0.95;
    SPECULAR = 0.08;
}
