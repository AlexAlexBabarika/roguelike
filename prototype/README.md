# Storm / Glyph Courtyard

A standalone **Godot 4.5.1** graphics demo with original geometry generated in
**headless Blender 4.5.3 LTS**, migrated from `noimnotahuman/demos/ascii-storm`.
See [migration provenance](../docs/MIGRATION.md) and the [research library](../docs/README.md).
No plot, NPCs, combat, admission mechanics, or backend: just a geometric player
running around a ruined courtyard in rain and wind.

This is a rendering proof of concept, not the proposed isometric forest/clinic
roguelite. The original repository is unchanged. The root README provides
commands that work from the repository root; commands below run inside `prototype/`.

## Separate forest / clinic art mock

The latest look-development scene is the
[clinic grove](../docs/CLINIC_GROVE.md): run `godot --path . res://clinic_grove.tscn`.
It uses artist-authored CC0 conifers, textured earth/rocks/ferns, dry daylight
and real shadows, without a screen filter. It remains separate from the playable
courtyard and the historical mocks below. Higher geometry cost, not a final
production or performance claim.

**1–3:** context / isolated tree / approach. **Q/E:** orbit. **Wheel:** zoom.
**I:** isolate. **S:** silhouette. **L:** shadows. **T:** weather. **Space:** pause.
**H:** HUD. Earlier `res://forest_slice.tscn` remains a historical procedural test.

Run `godot --path . res://mock_scene.tscn` for the new model and lighting study.
It does not change the courtyard main scene, player or effects. The traveler
is a static posed model, not a playable or rigged character.

**1–3:** wide / clinic / traveler. **Q/E:** orbit. **Wheel:** zoom.
**R:** rain. **F:** reflections. **Space:** freeze weather and orbit. **H:** HUD.
See the [mock-scene guide and engine captures](../docs/FOREST_CLINIC_MOCK.md).

## Run without opening an editor

Install the standard Godot 4.5.1 build for your OS, then from this directory:

```sh
godot --headless --editor --import
godot --path .
```

The first command imports assets and exits; it does not open an editor window.
The checked-in GLB and glyph atlas are sufficient to play. Blender and Python
are only needed when regenerating assets. The game has no network dependencies.

On Linux x86_64, optional pinned tool installation:

```sh
bash tools/setup_linux.sh
export PATH="$HOME/.local/bin:$PATH"
```

The helper downloads official releases and verifies their published checksums.
It requires `curl`, `unzip`, `tar`, and standard desktop OpenGL libraries.

## Controls

| Input             | Action                                    |
| ----------------- | ----------------------------------------- |
| WASD / arrow keys | Camera-relative movement                  |
| Shift             | Run                                       |
| Q / E             | Orbit camera                              |
| Mouse wheel       | Zoom                                      |
| 1 / 2 / 3 / 4     | Toggle glyphs / rain / wind / reflections |
| L                 | Toggle the player's lamp                  |
| R                 | Reset player position                     |
| H / Escape        | Hide / restore the HUD                    |

The four effects also have clickable buttons. Disable glyphs to compare the
actual 3D scene with the character treatment.

## How it is built

- `tools/build_scene.py` builds beveled masonry, an arch, bare trees, benches,
  coping stones, and a terrain opening in Blender, exporting `assets/courtyard.glb`.
- `player.gd` uses `CharacterBody3D`, camera-relative movement, collision,
  a simple procedural running gait, and a moving light.
- `main.gd` creates the world and two viewports. A mirrored camera renders the
  **same live world** into a lower-resolution reflection texture. Water samples
  this texture using projective coordinates, wave distortion, and step ripples.
  Separate visibility layers keep the ground and water out of the reflection pass.
- Instanced grass bends through a vertex shader; instanced geometric rain falls
  and drifts with wind. Storm lighting occasionally flashes.
- A canvas shader samples the offscreen scene into colored glyphs. Vegetation,
  water, and edges receive different glyph choices. This lightweight prototype
  uses color heuristics, **not a full material-ID buffer or world-anchored glyphs**.
- Uses Godot's Compatibility renderer. The lighting is rasterized and the water
  reflection is a second camera render: **not real-time ray tracing**.

## Rebuild assets

```sh
blender --background --python tools/build_scene.py
godot --headless --editor --import
```

Geometry is deterministic from seed 7301. No AI-generated images, downloaded
models, or Blender server are used at runtime. The included font atlas can be
regenerated with Pillow and a local monospace font:

```sh
python tools/build_glyphs.py /path/to/monospace.ttf
```

The included glyph atlas uses DejaVu Sans Mono; see `assets/FONT-LICENSE.txt`.

## Export a playable build

Install Godot's official 4.5.1 export templates. On Linux, this helper downloads
only the Web and Linux entries from the official archive (ZIP CRC-checked):

```sh
python tools/setup_exports.py
mkdir -p build/web build/linux
godot --headless --export-release Web build/web/index.html
godot --headless --export-release Linux build/linux/storm.x86_64
```

The Linux binary embeds its data and needs no editor. For the single-threaded
WebGL 2 build, serve `build/web` using any HTTP server; don't open `index.html`
through `file://`. No cross-origin isolation headers are required.

## Checks

```sh
godot --headless --editor --import
godot --headless --path . --script tests/smoke.gd
gdlint main.gd player.gd tests/*.gd
gdformat --check main.gd player.gd tests/*.gd
```

Install `gdtoolkit==4.5.0` for the optional GDScript lint/format commands.
The headless smoke checks exercise movement, collision, camera geometry,
effect toggles, reset, and the player lamp. Headless mode does **not** validate
shader appearance; a desktop render is necessary for that:

```sh
godot --path . --script tests/render.gd -- /absolute/path/storm.png
godot --path . --script tests/render.gd -- /absolute/path/storm-raw.png --verify
```

The `--verify` run checks actual reflection-texture brightness and rendered pixel
changes when reflections are disabled. CI runs it under Xvfb/software OpenGL
alongside the headless logic checks. It is not a substitute for human playtesting.

The scene uses a few thousand vegetation instances and an additional reflection
render. Performance on phones, WebGL, macOS, and Windows is not yet established;
this is a graphics proof of concept, not a production renderer.
