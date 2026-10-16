# Clinic grove — authored asset / daylight revision

This is the next visual candidate after the user rejected both the painted
I1 filter and the regular, tiered procedural spruces. The change is primarily
**better source assets and surface treatment**, not a shader that hides arbitrary
low-poly meshes. The playable `res://main.tscn` is unchanged.

![Actual Godot dry-daylight viewport](screenshots/clinic-grove/daylight.png)

## What changed

- Three CC0 **artist-authored Poly Haven conifers**, selected from their LOD2
  meshes: asymmetric crowns, small branchlets, natural gaps, textured bark
  and fixed needle geometry. These are not Valheim assets or AI meshes.
- Texture/normal-mapped leaf litter and moss on a slightly raised terrain edge;
  worn clearing, small grass blades, mossy rocks and four fern variants.
- Weathered projected wood, stained limewash, restrained slate-roof weathering,
  textured stone and less neon window color on the original clinic.
- Nineteen staggered tree placements frame an open approach. The **context
  camera is unchanged** from the earlier structured-forest capture so the
  result can be compared without a framing trick.
- Ordinary lit materials, alpha scissoring, mipmaps and directional shadows.
  Dry daylight is the default: no fog, rain, reflection pass, screen filter,
  depth-of-field, image generation or paint-over.

## Compare the actual engine output

![Earlier procedural slice versus current authored assets](boards/clinic-grove-comparison.jpg)

The board only resizes/arranges captures. Top row: identical orthographic
camera and resolution, **but assets, materials, dressing and light balance
all change**. This is not a controlled shader-only A/B experiment. Bottom:
an isolated tree and the approach camera. Originals and JSON sidecars:

- [Dry daylight context](screenshots/clinic-grove/daylight.png) / [provenance](screenshots/clinic-grove/daylight.json)
- [Isolated tree](screenshots/clinic-grove/tree.png) / [provenance](screenshots/clinic-grove/tree.json)
- [Same-tree silhouette](screenshots/clinic-grove/silhouette.png) / [provenance](screenshots/clinic-grove/silhouette.json)
- [Closer approach](screenshots/clinic-grove/approach.png) / [provenance](screenshots/clinic-grove/approach.json)
- [Optional weather, context camera](screenshots/clinic-grove/weather.png) / [provenance](screenshots/clinic-grove/weather.json)

Earlier [structured slice](STRUCTURED_FOREST.md), [rejected I1](PAINTED_FOREST.md)
and [G1/M1 experiments](style-study.md) remain intact as historical evidence.
The source and processed asset attribution is in the
[CC0 asset notes](../prototype/assets/reference-forest/README.md).

## Run / reproduce

```sh
make clinic-grove
# 1 context, 2 isolated tree, 3 approach; Q/E orbit; wheel zoom
# I isolate, S silhouette, L shadows, T weather, Space pause, H HUD

python3 prototype/tools/capture_clinic_grove.py
python3 docs/tools/build_clinic_grove_board.py
make grove-render-check
```

The checked-in assets suffice; rebuild instructions are in the asset notes.
Each capture records engine, renderer/device, orthographic camera, wind/weather/
shadow state, asset-manifest hashes, scene/shader hashes and the captured PNG
fingerprint. Native render checks verify actual light/shadow pixel changes,
visible terrain with upward-facing normals, texture mipmaps, deterministic
placements, wind uniforms, non-billboarding and optional weather/isolation.

## Honest limits

- This removes the old regular crown tiers and bare floor. It does **not**
  establish a finished Souls/Pathologic/NieR art direction: the cottage-like
  clinic silhouette and simple traveler remain the weakest, mismatched assets.
- Photo-derived foliage can shimmer at distance. These checks do not establish
  subtle temporal stability or full combat readability; no combat is added.
- About **1.04M full-detail tree triangles** across nineteen placements before
  Godot's generated LODs, versus roughly 154k in the earlier seven-tree slice.
  Better source geometry is doing real work here; this is not a free shader fix.
- Compatibility/llvmpipe screenshots demonstrate renderer behavior only.
  Target-device frame time, memory, alpha overdraw and production LOD budgets
  remain unvalidated. Do not adopt the whole grove as an optimized game level.
- The optional weather view is secondary evidence, not a way to conceal the
  daylight asset quality. The default game launch is still the playable demo.
