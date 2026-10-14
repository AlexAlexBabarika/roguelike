# Migration provenance

## Godot prototype

- Source repository: [AlexAlexBabarika/noimnotahuman](https://github.com/AlexAlexBabarika/noimnotahuman).
- Original implementation: [PR #27](https://github.com/AlexAlexBabarika/noimnotahuman/pull/27).
- Source revision: [`f38ac8fc346e93c481e687913c7078e626cc8bcc`](https://github.com/AlexAlexBabarika/noimnotahuman/commit/f38ac8fc346e93c481e687913c7078e626cc8bcc).
- Source directory: `demos/ascii-storm/`; destination: `prototype/`.

The migration copies all 32 tracked prototype files: engine configuration,
scene/scripts, shaders, import metadata and UIDs, original generated GLB,
glyph atlas and font license, export presets, Blender/Python setup tools and
Godot smoke/render tests. The prototype README is adapted to the new repository;
the runtime scripts, shaders and asset-generation logic are unchanged.

The new root Makefile and CI run the checks at the new path. No files are removed
or modified in the source repository. Its unrelated browser-based hospital
game is not copied.

Excluded: `.godot/`, exported Web/Linux builds, Python bytecode, temporary
Blender files and machine-specific caches. Exports are reproducible using the
preserved scripts and presets rather than checked-in executables.

## Reports and boards

Source: [the original design/research session](https://app.devin.ai/sessions/7bf89cb899334858a5f720f8dcdd9854).
The six complete HTML reports and four final comparison boards are copied
without content changes. The inventory and SHA-256 fingerprints are in
`manifest.json`. Intermediate report fragments, duplicate renders, scratch
scripts, downloaded reference-image originals and validation screenshots/logs
are not archived; the full reports already embed their required images.

The Last Window report is retained as historical graphics research, not as
the current setting or game design. Later reports supersede earlier
recommendations without retroactively rewriting them.

## Attribution and limitations

AI-generated concept studies are not engine renders or production-ready
assets. Third-party inspiration images and design sources remain credited in
the reports. Inclusion in a research report does not grant permission to reuse
those third-party images as game assets.

The glyph atlas uses DejaVu Sans Mono; its license remains in
`prototype/assets/FONT-LICENSE.txt`. Godot and Blender have their own licenses;
this repository does not include their application binaries. Distributable
exports require the applicable engine and font notices.

The reports describe unimplemented proposals. The graphics demo does not
validate future combat, art-direction shaders, hardware/mobile performance or
the game loop's fun and horror hypotheses.
