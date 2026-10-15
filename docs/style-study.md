# Two same-camera material and atmosphere experiments

This executes [section 5 of the supplied decision memo](https://claude.ai/artifact/WhxyRbbddQWDswchqX1Lqy), not a final art-direction selection. All source renders are actual Godot output. The separate look-development scene does not replace the playable courtyard or the original forest/clinic mock.

Open the [standalone interactive comparison](boards/style-study-comparison.html) for matched arm/camera/resolution and accessibility views; download the HTML to use it offline.

## Follow-up after visual rejection

The user rejected G1 as still looking low-poly. The stronger **I1 painted-forest follow-up** adds silhouette replacement and a selective screen filter: [new matched board, implementation and limitations](PAINTED_FOREST.md). G1 below is only the historical provisional choice for the controlled atmosphere experiment, not an accepted final style.

## Original two-test decision

1. **Keep the shared preparation.** Unifying bough pigments, shortening exposed trunk tips, smoothing the cloak and reducing roof/coat palette variation make a clearer improvement than changing the lighting model alone.
2. **Use G1, provisionally, for the atmosphere experiment.** Wet gouache preserves/improves the sampled traveler/path value contrast. Miniature reduces it below baseline and is not the safer choice on these meshes. This is one reviewer's choice, not the proposed three-person unlabelled preference study.
3. **Do not adopt G1+H unchanged.** Its brighter floor helps the dark enemy probe, but reduces traveler/path contrast. None of the arms meets the proposal's minimum 15-level crown/roof/floor separation. Pointed crowns and repeated frond silhouettes remain visible.
4. **No selective blur in the original two tests.** The optional W+H+S arm was not run. I1 is a separate follow-up after that result was rejected; its static prototype mask is not a validated production gameplay layer.

## Arms and controls

| Arm | Kit | Materials | Additional atmosphere |
| --- | --- | --- | --- |
| A0 | Unmodified original GLB | Current mock | No |
| A1 | Prepared GLB | Current material path | No |
| G1 | Same prepared GLB | Wrapped gouache, broad world-rest-position pigment | No |
| M1 | Same prepared GLB | Wrapped Lambert miniature, no pigment pattern | No |
| G1H / W+H | Same prepared GLB | G1 frozen | Floor/forest re-key, distance haze, wet roof/puddles |

Test 1 retains the existing ground and reflection shaders. Actor materials receive no pigment variation; windows, enemy and warning probes remain clean. All lights, positions and energies, tone mapping, fog density 0.004, ambient energy 0.28 and 4× MSAA remain fixed. Still clock: 6 seconds. Seed: 40217. All three cameras at 1920×1080 and 1280×720, plus wide dry and no-wind diagnostics per arm. Rain, wind and reflections are enabled otherwise. Per-capture JSON records the exact cameras, lights, flags, asset hash and driver.

G1H raises the floor, darkens forest interiors, lowers rocks, adds sky Fresnel/wet puddle edges, and adds focus-relative haze beyond approximately 12 m. Its intended special roof gradient did not bind because no mesh group was named `Roof`; I1 fixes classification independently without changing historical G1H captures. Actors and warnings are excluded from that new material haze; the original global engine fog remains identical in every arm. The new distance layer is radial from a fixed play focus, not screen-depth volumetric fog.

The small dark capsule and pale warning sector are **non-gameplay readability probes**. Their simple opaque shapes do not validate enemy facing, actual telegraph colors/animation, combat, navigation or occlusion handling.

## Shared preparation, not shader credit

`prepare_style_kit.py` reuses the original generator without overwriting its export. It produces a separate `forest-clinic-prepared.glb` and metadata:

- One pigment per four-triangle bough: 4,840 fronds.
- Hide the upper tips of 22 tall trunks inside crowns.
- Radial/axial proxy normals for spruce boughs and smooth cloak/sleeve normals.
- Consistent roof/coat/window palette and lower rock values.
- Analytic vertex masks: R approximate interior occlusion, G normal/exposure wetness, B reserved wear (zero), A object pigment seed.
- Explicit remapping of the authored Blender color attribute to `COLOR_0`, normalized 8-bit RGBA; no white placeholder channel.

These masks are not baked AO or shelter raycasts. Architecture retains its existing hard planar normals and bevels rather than receiving a new generic 40-degree weighted-normal pipeline. No new UVs, textures, decimation, texture-atlas cleanup, rigging or AI-mesh repair was tested. A1 deliberately contains the palette/normal preparation too, so its improvement is not attributed to gouache.

## Captures and diagnostics

- [Raw stills and capture metadata](screenshots/style-study/).
- `test1-provenance.json`, `test2-provenance.json`, `anchor-provenance.json`: commands, Godot version/driver, source and image hashes, camera and weather state.
- `motion-provenance.json`: 15 offline clips: A0/A1/G1/M1/G1H × orbit/weather/zoom. Videos and frame sequences are regenerated under ignored `artifacts/style-study/`, not embedded into the raw-PNG archive.
- The six labelled, downscaled/lossy animated comparisons below are review derivatives, not measurement inputs. Test 1 panels are 480×270 each; Test 2 panels are 640×360, both retaining the 15 Hz sequence. `motion-boards.json` links each to its source-video hash.
- `metrics.json`: normalized sample rectangles, linear Rec.709 luminance, signed contrasts, color-vision simulation matrices and anchored-pattern diagnostic.

| Motion | Test 1: A0 / A1 / G1 / M1 | Test 2: G1 / G1H |
| --- | --- | --- |
| Wide orbit | [Open animation](screenshots/style-study/test1-orbit-comparison.webp) | [Open animation](screenshots/style-study/test2-orbit-comparison.webp) |
| Clinic weather | [Open animation](screenshots/style-study/test1-weather-comparison.webp) | [Open animation](screenshots/style-study/test2-weather-comparison.webp) |
| Traveler zoom | [Open animation](screenshots/style-study/test1-zoom-comparison.webp) | [Open animation](screenshots/style-study/test2-zoom-comparison.webp) |

Interactive G1/M1 inspection and sampled review of all 15 clips found no gross movement/deformation on static architecture and no obvious large-scale pigment sliding. Rain remained narrow rather than broadly blurred. Minor foliage-edge aliasing was visible in G1/G1H weather; the blade loses shape/disappears as every arm zooms out. **Subtle shimmer, foliage/reflection stability and sub-pixel crawling remain inconclusive**, not passed: these are short offline samples and the live software renderer responded slowly. Pointed/repeated foliage stays busy; blade and probes are weakest at wide framing. Camera presets, orbit, zoom, rain, freeze and HUD controls responded in both arms.

The standalone comparison was checked in Chrome at desktop and 375 px, light/dark, offline, reduced motion, keyboard navigation, all control options and a recoverable decode-error state. Default portrait printing initially clipped columns; corrected wrapping/fixed-width print rules now show all eight columns and five rows. No real empty-data UI path exists to validate.

Motion uses 120 deterministically sampled frames over eight seconds at 15 Hz: wide orbit −0.5 → +0.5 radians, static clinic rain/wind, and traveler orthographic size 5.0 → 13.5. This is **offline image-sequence sampling**, not a claim that the scene runs at 15 FPS. The last weather sample is 13.933 seconds; the encoded video duration is 8 seconds. Orbit endpoints and zoom endpoints are included.

The anchoring test isolates the emission-only pigment on a static roof with rain, wind and reflections disabled and a 64-pixel camera translation. An initial diagnostic mixed logical screen coordinates with physical PNG pixels; the apparatus was corrected using the orthographic camera size and rendered texture height, then rerun. Normal stills and motion have zero pan and are unaffected.

The corrected aligned mean absolute error is **0.00735 / 255**, versus **19.37734 / 255** without alignment. One ordinary zero-pan G1 capture was also repeated after the diagnostic correction and was byte-identical to its archived PNG. The earlier phase manifests preserve their historical controller hashes; the changed branch only runs for the pan diagnostic.

### Measurement interpretation

Luminance is computed by linearizing sRGB, applying Rec.709 coefficients (0.2126, 0.7152, 0.0722), averaging a fixed rectangle, and encoding that mean back to sRGB 0–255. Local contrast is the signed difference between two such means, not WCAG contrast. The proposed 15-level mass separation is evaluated on the same three rectangles in every arm. Roof edge energy is neighboring-pixel absolute difference in one interior roof crop; lower is not automatically better art.

The rectangles are hand-picked and shown in the interactive report. They are not semantic segmentation or a perceptual quality model; the crown includes interior gaps and the floor includes small grass details. Blade percentiles include background and cannot prove a minimum two-pixel silhouette. A clean static warning is a best-case cue, not validation of a moving or fading warning.

Greyscale uses the same linear Rec.709 conversion. Protan, deutan and tritan diagnostic views use the Machado et al. 2009 severity-1.0 matrices in linear RGB, clipped to display gamut. They are simulations, not participant accessibility validation. Engine PNGs remain untouched; report JPEGs, sampling maps and simulated views are explicitly derived displays.

## Reproduce

Requirements: existing Godot 4.5.1 / Blender 4.5.3 setup, Xvfb, FFmpeg, Python with NumPy and Pillow. No new runtime game dependency.

```sh
blender --background --python prototype/tools/prepare_style_kit.py
make import
python3 prototype/tools/capture_style_study.py test1
python3 prototype/tools/capture_style_study.py test2 --winner G1
python3 prototype/tools/capture_style_study.py motion --winner G1
python3 prototype/tools/capture_style_study.py anchor
python3 prototype/tools/capture_style_study.py provenance
python3 prototype/tools/capture_style_study.py boards --winner G1
python3 prototype/tools/analyze_style_study.py
python3 prototype/tools/style_study_report.py
make check
make render-check
pre-commit run --all-files
```

`make style-study` opens G1 interactively. For another arm:

```sh
godot --path prototype res://style_study.tscn -- --arm=M1
godot --path prototype res://style_study.tscn -- --arm=G1 --atmosphere
```

Original camera/weather controls still work: 1/2/3 views, Q/E orbit, wheel zoom, R rain, F reflections, Space freeze, H HUD. `--no-probes` hides the non-gameplay comparison props. The standalone HTML is compiled from the generated body using the bundled Devin interactive-artifact kit; its inline data and controls work without a server or network.

## Evidence still missing

- Representative licensed AI-generated meshes, including bad normals/UVs, texture atlases, alpha cards and animation.
- Weakest target GPU/device, frame budget, memory budget and an actual real-time profile. Local renderer: **Mesa llvmpipe software OpenGL**, not target hardware.
- Three-or-more-person unlabelled preference selection and player/accessibility testing.
- Animated enemy facing, actual warning/attack effects, camera occlusion, rapid combat motion and production foliage.

Shaders cannot add pixels outside existing triangle coverage. Better crown/grass silhouettes and more varied forest layout remain the next geometry task, not evidence that either shader can hide arbitrary low-poly models.
