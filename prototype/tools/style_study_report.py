"""Build a standalone comparison body from actual engine captures and measurements."""

import base64
import io
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
FRAMES = ROOT / "docs/screenshots/style-study"
ARTIFACTS = ROOT / "artifacts/style-study"


def embedded(path):
    image = Image.open(path).convert("RGB")
    image.thumbnail((1280, 720))
    stream = io.BytesIO()
    image.save(stream, format="JPEG", quality=82)
    return "data:image/jpeg;base64," + base64.b64encode(stream.getvalue()).decode()


def main():
    metrics = json.loads((FRAMES / "metrics.json").read_text())
    images = {p.stem: embedded(p) for p in FRAMES.glob("*.png")
              if not any(part in p.name for part in ["anchor", "dry", "no-wind"])}
    names = {"A0": "A0 · baseline", "A1": "A1 · prep only", "G1": "G1 · wet gouache",
             "M1": "M1 · soft miniature", "G1H": "G1 + atmosphere", "M1H": "M1 + atmosphere"}
    columns = [("crown", "Crown"), ("roof", "Roof"), ("ground", "Open floor"),
               ("cloak_path_delta", "Cloak − path"), ("enemy_floor_delta", "Floor − enemy"),
               ("crown_roof_ground_min_gap", "Minimum mass gap"), ("roof_edge_energy", "Roof edge energy")]
    headers = "".join(f'<th scope="col" data-numeric>{label}</th>' for _, label in columns)
    rows = ""
    for arm, data in metrics["arms"].items():
        cells = "".join(f'<td data-numeric>{data["color"][key]:.{3 if key == "roof_edge_energy" else 2}f}</td>'
                        for key, _ in columns)
        rows += f'<tr><th scope="row">{names[arm]}</th>{cells}</tr>'
    matrix = json.dumps(metrics["matrices"])
    winner = "G1" if "G1H" in metrics["arms"] else "M1"
    anchor = metrics.get("anchor", {})
    body = '''
<section class="a-section">
  <div class="a-callout a-callout--decision"><strong>Read the experiment, not a finished art direction.</strong>
  Shared mesh preparation removes much of the roof checker and cloak striping. Material shading can unify surfaces, but the pointed fronds and repeated silhouettes remain geometry problems. Atmosphere must be judged against the loss of local traveler contrast.</div>
  <p class="a-prose">Actual Godot 4.5.1 Compatibility renders, one Mesa llvmpipe machine. The kit is procedurally authored in Blender—not an inspected set of AI-generated meshes. No target-hardware performance conclusion is possible.</p>
  <p class="a-prose"><strong>Test 1:</strong> G1 is the provisional choice for Test 2: its sampled cloak/path contrast improves on baseline; M1 reduces it. Neither achieves the proposed 15-level separation of crown, roof and floor. <strong>Test 2:</strong> the brighter floor reaches the requested range and improves the dark enemy probe, but roughly halves traveler/path contrast. Do not adopt the atmosphere arm unchanged.</p>
</section>
<section class="a-section">
  <h2 class="a-section__title">Matched-camera comparisons</h2>
  <p class="a-section__note">Display images are JPEG/downscaled derivatives of archived untouched PNGs. Greyscale and color-vision views are derived diagnostics, not engine output or in-game postprocessing.</p>
  <div class="a-panel" style="padding:1rem">
    <div class="controls">
      <label>Left arm <select id="left"></select></label>
      <label>Right arm <select id="right"></select></label>
      <label>Camera <select id="view"><option>wide</option><option>clinic</option><option>traveler</option></select></label>
      <label>Source resolution <select id="size"><option>1920x1080</option><option>1280x720</option></select></label>
      <label>Diagnostic <select id="mode"><option value="color">Color</option><option value="grey">Rec.709 greyscale</option><option value="deutan">Deutan simulation</option><option value="protan">Protan simulation</option><option value="tritan">Tritan simulation</option></select></label>
    </div>
    <div class="controls"><button type="button" id="pair1">Test 1 · gouache / miniature</button><button type="button" id="pair2">Test 2 · winner / atmosphere</button></div>
    <div class="a-grid a-grid--halves">
      <figure><canvas id="canvas-left" role="img"></canvas><figcaption id="label-left"></figcaption></figure>
      <figure><canvas id="canvas-right" role="img"></canvas><figcaption id="label-right"></figcaption></figure>
    </div><p class="a-section__note" id="status" role="status" aria-live="polite"></p>
  </div>
</section>
<section class="a-section">
  <h2 class="a-section__title">Descriptive luminance samples</h2>
  <p class="a-section__note">1080p wide view only. Linear-light Rec.709 means encoded back to sRGB 0–255; contrasts are signed differences in those units. The minimum crown/roof/floor pairwise gap should reach 15 according to the proposal. Edge energy is mean absolute neighboring-pixel difference, not a universal quality metric. These rectangles do not segment objects.</p>
  <div class="a-table-scroll"><table class="a-table" data-a-sticky-columns="1"><caption>Identical sample rectangles across all arms</caption><thead><tr><th scope="col">Arm</th>HEADERS</tr></thead><tbody>ROWS</tbody></table></div>
  <details class="a-disclosure"><summary>Sampling map and methods</summary><img class="roi-map" alt="Labelled measurement rectangles on the baseline wide capture" src="ROI_MAP"><p>Small rectangles can include shadow, ground or an edge; inspect this map before interpreting the numbers. Color-vision simulations use Machado 2009 severity 1.0 matrices in linear RGB and clip to the display gamut. They do not substitute for testing with color-blind players.</p></details>
</section>
<section class="a-section">
  <h2 class="a-section__title">Controls and evidence boundaries</h2>
  <ul class="a-prose"><li>A0 uses the original GLB. A1, G1 and M1 use exactly the same prepared GLB. The default playable courtyard and previous captures are untouched.</li>
  <li>All stills freeze the weather clock at 6 s, with rain, wind and reflections on. Fog density 0.004, ambient 0.28, MSAA 4×, lights and orthographic camera presets are unchanged.</li>
  <li>Dry and no-wind wide diagnostics are archived separately. Motion captures use a deterministic 15 Hz sampling clock over 8 s: wide ±0.5 rad orbit, fixed clinic with weather, and traveler 5.0 → 13.5 zoom. These are offline renders—not evidence of real-time 15 FPS.</li>
  <li>The dark capsule and pale warning sector are labelled non-gameplay probes. No enemy animation, facing, actual attack warning, AI-mesh robustness, occlusion solution or target-device frame budget has been validated.</li>
  <li>Mask channels are analytic approximations, not baked AO or ray-traced rain shelter. Edge-wear is reserved at zero. Existing architecture bevels/hard normals are retained; the study does not claim a general AI-mesh cleanup pipeline.</li></ul>
  <p class="a-prose">Static pigment anchoring: aligned MAE ANCHOR on a 0–255 scale in an emission-only roof diagnostic after a 64 px camera pan. This isolates pattern anchoring, not all foliage or reflection temporal behavior.</p>
  <div class="a-callout a-callout--risk"><strong>Still needed:</strong> raw licensed AI mesh exports, the weakest supported hardware and frame budget, and the proposed three-or-more-person unlabelled preference comparison. One reviewer’s visual choice is provisional.</div>
</section>
<style>
.controls{display:flex;flex-wrap:wrap;gap:1rem;margin-bottom:1rem}.controls label{display:flex;flex-direction:column;gap:.3rem}.controls select,.controls button{font:inherit;max-width:100%;padding:.4rem}figure{margin:0;min-width:0}canvas,.roi-map{width:100%;height:auto;display:block}figcaption{padding-top:.5rem}.a-table{white-space:nowrap}
@media print{
  .controls{display:none}
  .a-table-scroll{overflow:visible!important;width:100%;max-width:100%}
  .a-table{width:100%;min-width:0!important;table-layout:fixed;white-space:normal;font-size:8pt}
  .a-table th,.a-table td{padding:4pt;overflow-wrap:anywhere;min-width:0;white-space:normal}
  .a-table th:first-child{width:18%}
}
</style>
<script>
(()=>{
const images=IMAGES;
const names=NAMES;
const matrices=MATRICES;
const winner=WINNER;
const studyElement=id=>document.getElementById(id);
for(const side of ['left','right'])for(const [value,label] of Object.entries(names)){
  if(!images[value+'-wide-1920x1080'])continue;
  const option=document.createElement('option');option.value=value;option.textContent=label;studyElement(side).append(option);
}
studyElement('left').value='G1';studyElement('right').value='M1';
let revision=0;
const linear=c=>c<=.04045?c/12.92:((c+.055)/1.055)**2.4;
const encode=c=>{c=Math.max(0,Math.min(1,c));return 255*(c<=.0031308?c*12.92:1.055*c**(1/2.4)-.055)};
async function draw(side,token){
  const arm=studyElement(side).value,view=studyElement('view').value,size=studyElement('size').value,mode=studyElement('mode').value;
  const image=new Image();image.src=images[arm+'-'+view+'-'+size];await image.decode();if(token!==revision)return;
  const canvas=studyElement('canvas-'+side);canvas.width=image.width;canvas.height=image.height;
  const context=canvas.getContext('2d',{willReadFrequently:true});context.drawImage(image,0,0);
  if(mode!=='color'){
    const pixels=context.getImageData(0,0,canvas.width,canvas.height),d=pixels.data;
    for(let i=0;i<d.length;i+=4){const r=linear(d[i]/255),g=linear(d[i+1]/255),b=linear(d[i+2]/255);
      if(mode==='grey'){const y=encode(.2126*r+.7152*g+.0722*b);d[i]=d[i+1]=d[i+2]=y;}
      else{const m=matrices[mode];d[i]=encode(m[0][0]*r+m[0][1]*g+m[0][2]*b);d[i+1]=encode(m[1][0]*r+m[1][1]*g+m[1][2]*b);d[i+2]=encode(m[2][0]*r+m[2][1]*g+m[2][2]*b);}
    }context.putImageData(pixels,0,0);
  }
  const label=names[arm]+' · '+view+' · '+size+' · '+mode;studyElement('label-'+side).textContent=label;canvas.setAttribute('aria-label',label);
}
async function update(){const token=++revision;studyElement('status').textContent='Rendering comparison…';try{await Promise.all([draw('left',token),draw('right',token)]);if(token===revision)studyElement('status').textContent='Both arms share the selected camera, clock and source resolution.';}catch(error){if(token===revision)studyElement('status').textContent='Could not draw this comparison. Try another selection.';console.error(error);}}
for(const id of ['left','right','view','size','mode'])studyElement(id).addEventListener('change',update);
studyElement('pair1').onclick=()=>{studyElement('left').value='G1';studyElement('right').value='M1';update()};
studyElement('pair2').onclick=()=>{studyElement('left').value=winner;studyElement('right').value=winner+'H';update()};
update();
})();
</script>
'''
    replacements = {"HEADERS": headers, "ROWS": rows, "ROI_MAP": embedded(ARTIFACTS / "A0-roi-map.jpg"),
                    "ANCHOR": f'{anchor.get("aligned_mae_0_255", float("nan")):.4f}',
                    "IMAGES": json.dumps(images), "NAMES": json.dumps(names), "MATRICES": matrix,
                    "WINNER": json.dumps(winner)}
    for key, value in replacements.items():
        body = body.replace(key, value)
    (ARTIFACTS / "report-body.html").write_text(body)


if __name__ == "__main__":
    main()
