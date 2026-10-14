shader_type canvas_item;
render_mode unshaded;

uniform sampler2D scene_texture : filter_linear, repeat_disable;
uniform sampler2D glyph_atlas : filter_nearest, repeat_disable;
uniform vec2 grid_size = vec2(160.0, 80.0);
uniform bool ascii_enabled = true;

void fragment() {
    if (!ascii_enabled) {
        COLOR = texture(scene_texture, UV);
    } else {
        vec2 cell = floor(UV * grid_size);
        vec2 sample_uv = (cell + 0.5) / grid_size;
        vec3 source = texture(scene_texture, sample_uv).rgb;
        float brightness = dot(source, vec3(0.2126, 0.7152, 0.0722));
        vec3 left = texture(scene_texture, sample_uv - vec2(1.0 / grid_size.x, 0.0)).rgb;
        vec3 above = texture(scene_texture, sample_uv - vec2(0.0, 1.0 / grid_size.y)).rgb;
        float dx = brightness - dot(left, vec3(0.2126, 0.7152, 0.0722));
        float dy = brightness - dot(above, vec3(0.2126, 0.7152, 0.0722));
		float density = smoothstep(0.025, 0.65, brightness);
		float index = clamp(floor(pow(density, 0.75) * 11.0), 0.0, 11.0);
        bool vegetation = source.g > source.r * 1.22 && source.g > source.b * 1.08;
        bool water = source.b > source.r * 1.4 && brightness < 0.19;
        if (vegetation && brightness > 0.035) {
            index = 12.0 + mod(cell.x * 3.0 + cell.y * 7.0, 4.0);
		} else if (water && brightness > 0.12) {
            index = 16.0 + mod(cell.x + cell.y, 2.0);
        } else if (abs(dx) + abs(dy) > 0.09 && brightness > 0.09) {
            index = abs(dx) > abs(dy) ? 18.0 : 19.0;
        }
        vec2 local = fract(UV * grid_size);
        float ink = texture(glyph_atlas, vec2((index + local.x) / 20.0, local.y)).r;
        vec3 color = source * (0.20 + ink * 1.55);
        color += vec3(0.007, 0.009, 0.014);
        float vignette = 1.0 - smoothstep(0.25, 0.77, length(UV - 0.5)) * 0.32;
        COLOR = vec4(color * vignette, 1.0);
    }
}
