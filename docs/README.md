# Research library

All six complete reports from the design exploration are archived here,
including their embedded images, source links and interactive controls. They
are preserved byte-for-byte from the delivered reports; `manifest.json`
records their SHA-256 fingerprints and the supporting boards.

Download an HTML file and open it locally. GitHub displays its source, not the
rendered report. These documents work offline; following an external source
link naturally requires a connection. Print mode reveals the alternate views
in the reports, including the game-loop report's optional detail sections.

## Current decisions and proposals

| Report | Scope | Status |
| --- | --- | --- |
| [Combat, combinations and dread](reports/game-loop-design-report.html) | Exact mechanics brief; combat/build/run rules; progression, horror pacing and prototype gates; nine source entries and an interactive synergy example. | Design proposal, not implemented or approved. |
| [Four new artistic directions](reports/new-art-directions.html) | Storm Fresco, Woven Blight, Amber Archive and Cold Flash, with forest/clinic combat studies and credited inspiration. | Current art shortlist; no final selection. |
| [Art direction for affordable models](reports/shader-production-guide.html) | What simplified geometry and shaders can conceal; concrete Blender/Godot production recipes for the four new styles. | Production research; not tested shader output. |

## Earlier explorations

| Report | Scope | Why keep it |
| --- | --- | --- |
| [Stormbound isometric art directions](reports/isometric-art-directions.html) | Porcelain Night, Woodcut Weather, Cut-paper Nocturne and Afterimage evaluated for combat, rain and multiplier effects. | Records the transition from scenic tests to action-game readability. |
| [An original visual language](reports/art-directions.html) | Four non-ASCII alternatives, their material rules and Blender/Godot trade-offs. | Earlier construction-language research, not the current shortlist. |
| [The Last Window: artistic directions](reports/last-window-art-directions.html) | Carbon Witness, Sodium Noir and Signal Gothic for the earlier admission-game pitch. | Historical graphics exploration only; its setting and mechanics are superseded. |

## Comparison boards

- [Storm Fresco: actual Godot A/B/C comparison](boards/storm-fresco-engine-comparison-board.jpg) —
  derived from captured PNGs; [selected originals, measurements and limitations](STORM_FRESCO.md).
- [Four new styles](boards/new-art-directions-board.jpg)
- [Isometric combat studies](boards/isometric-art-directions-board.jpg)
- [Earlier non-ASCII alternatives](boards/art-directions-board.jpg)
- [Historical Last Window studies](boards/three-directions.png)

The four earlier boards are AI-generated concept comparisons, not Godot
screenshots or production assets. The Storm Fresco board is separate engine
look-dev evidence; it does not validate combat motion or performance.
Individual reports distinguish concept studies from
credited third-party references. Source links and limitations are retained.

## What this archive does not imply

- No final art direction, game title, run architecture or combat system has
  been approved merely by archiving the reports.
- The courtyard in `prototype/` is a graphics demonstration, not a completed
  forest/clinic environment or a playable roguelite.
- Shaders do not repair broken silhouettes, rigging or attack animation.
- The existing reflection technique is a second live camera render, not
  real-time ray tracing.

For source revision, licensing boundaries and what was excluded, see
[migration provenance](MIGRATION.md).
