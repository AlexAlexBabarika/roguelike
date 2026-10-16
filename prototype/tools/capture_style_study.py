"""Matched actual Godot captures. No image treatment is applied to raw frames."""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs/screenshots/style-study"
ARTIFACTS = ROOT / "artifacts/style-study"


def run(arm, view, size, *, suffix="", options=(), movie="", fps=15):
    label = f"{arm}{suffix}-{view}-{size}"
    destination = OUTPUT / f"{label}.png"
    if movie:
        destination = ARTIFACTS / "frames" / label
        destination.mkdir(parents=True, exist_ok=True)
    log = ARTIFACTS / f"{label}.log"
    command = ["xvfb-run", "-a", "godot", "--audio-driver", "Dummy", "--disable-vsync",
               "--resolution", size, "--path", str(ROOT / "prototype"),
               "res://style_study.tscn", "--", f"--arm={arm}", f"--view={view}",
               f"--capture={destination}", f"--fps={fps}", *options]
    if movie:
        command.append(f"--movie={movie}")
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            timeout=1800)
    log.write_text(result.stdout)
    if result.returncode or re.search(r"SCRIPT ERROR:|SHADER ERROR:|^ERROR:", result.stdout, re.M):
        raise RuntimeError(f"{label}: see {log}\n{result.stdout[-6000:]}")
    record = json.loads(Path(str(destination) + ".json").read_text())
    driver = next(line for line in result.stdout.splitlines() if "Using Device:" in line)
    version = next(line for line in result.stdout.splitlines() if line.startswith("Godot Engine v"))
    record["driver"] = driver
    record["godot_version"] = version.split("Godot Engine v", 1)[1].split(" - ", 1)[0]
    record["command"] = command
    if movie:
        video = ARTIFACTS / f"{label}.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(fps),
                        "-i", str(destination / "%04d.png"), "-c:v", "libx264",
                        "-crf", "18", "-pix_fmt", "yuv420p", str(video)], check=True)
        record["file"] = str(video.relative_to(ROOT))
        record["sha256"] = hashlib.sha256(video.read_bytes()).hexdigest()
        record["frame_sha256"] = [hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in sorted(destination.glob("*.png"))]
        record["encoded_video"] = json.loads(subprocess.check_output([
            "ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
            "stream=width,height,nb_frames,r_frame_rate,duration", "-of", "json", str(video)
        ], text=True))["streams"][0]
    else:
        record["file"] = str(destination.relative_to(ROOT))
        record["sha256"] = hashlib.sha256(destination.read_bytes()).hexdigest()
    print(label, "OK", flush=True)
    return record


def annotate_previous_captures():
    for phase in ["test1", "test2", "anchor", "motion"]:
        path = OUTPUT / f"{phase}-provenance.json"
        if not path.exists():
            continue
        provenance = json.loads(path.read_text())
        versions = set()
        for record in provenance["captures"]:
            log = ARTIFACTS / f'{Path(record["file"]).stem}.log'
            text = log.read_text()
            version = next(line for line in text.splitlines() if line.startswith("Godot Engine v"))
            record["godot_version"] = version.split("Godot Engine v", 1)[1].split(" - ", 1)[0]
            versions.add(record["godot_version"])
            if record["movie"]:
                frames = sorted((ARTIFACTS / "frames" / Path(record["file"]).stem).glob("*.png"))
                if len(frames) != len(record["frames"]):
                    raise ValueError(f"Frame count mismatch: {record['file']}")
                record["frame_sha256"] = [hashlib.sha256(frame.read_bytes()).hexdigest() for frame in frames]
                encoded = json.loads(subprocess.check_output([
                    "ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                    "stream=width,height,nb_frames,r_frame_rate,duration", "-of", "json",
                    str(ROOT / record["file"])], text=True))["streams"][0]
                record["encoded_video"] = encoded
        if len(versions) != 1:
            raise ValueError(f"Mixed Godot versions in {phase}: {versions}")
        provenance["godot_version"] = versions.pop()
        path.write_text(json.dumps(provenance, indent=2) + "\n")


def build_motion_boards(winner):
    boards = []
    labels = {"A0": "baseline", "A1": "prep only", "G1": "gouache", "M1": "miniature",
              winner + "H": "winner + atmosphere"}
    for movie, view in [("orbit", "wide"), ("weather", "clinic"), ("zoom", "traveler")]:
        for test, arms in [("test1", ["A0", "A1", "G1", "M1"]), ("test2", [winner, winner + "H"])]:
            inputs, filters, sources = [], [], []
            width = 480 if len(arms) == 4 else 640
            height = width * 9 // 16
            for i, arm in enumerate(arms):
                path = ARTIFACTS / f"{arm}-{movie}-{view}-1280x720.mp4"
                inputs.extend(["-i", str(path)])
                filters.append(f"[{i}:v]scale={width}:{height},setsar=1,drawtext=text='{arm} - {labels[arm]}':"
                               f"x=10:y=10:fontsize=16:fontcolor=white:box=1:boxcolor=black@0.8[v{i}]")
                sources.append({"file": str(path.relative_to(ROOT)),
                                "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
            layout = "0_0|w0_0|0_h0|w0_h0" if len(arms) == 4 else "0_0|w0_0"
            streams = "".join(f"[v{i}]" for i in range(len(arms)))
            filters.append(f"{streams}xstack=inputs={len(arms)}:layout={layout}[board]")
            output = OUTPUT / f"{test}-{movie}-comparison.webp"
            subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filters),
                            "-map", "[board]", "-c:v", "libwebp_anim", "-quality", "70",
                            "-compression_level", "4", "-loop", "0", str(output)], check=True)
            boards.append({"file": str(output.relative_to(ROOT)), "test": test, "movie": movie,
                           "panel_pixels": [width, height], "source_resolution": [1280, 720],
                           "sha256": hashlib.sha256(output.read_bytes()).hexdigest(), "sources": sources})
    (OUTPUT / "motion-boards.json").write_text(json.dumps({
        "kind": "Derived, downscaled/lossy motion comparisons; labelled, no masking or blur.",
        "clock": "15 Hz offline sampling over eight seconds, not target-device performance.",
        "boards": boards}, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["test1", "test2", "motion", "anchor", "provenance", "boards",
                                         "painted", "painted-motion"])
    parser.add_argument("--winner", choices=["G1", "M1"], default="G1")
    parser.add_argument("--fps", type=int, default=15)
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    if args.phase == "provenance":
        annotate_previous_captures()
        return
    if args.phase == "boards":
        build_motion_boards(args.winner)
        return
    records = []
    if args.phase == "painted":
        for size in ["1920x1080", "1280x720"]:
            for view in ["wide", "clinic", "traveler"]:
                records.append(run("I1", view, size))
        for view in ["wide", "traveler"]:
            records.append(run("I1", view, "1920x1080", suffix="-no-paint", options=("--no-paint",)))
    elif args.phase == "painted-motion":
        for movie, view in [("orbit", "wide"), ("weather", "clinic"), ("zoom", "traveler")]:
            records.append(run("I1", view, "1280x720", suffix="-" + movie, movie=movie, fps=args.fps))
    elif args.phase in ["test1", "test2"]:
        arms = ["A0", "A1", "G1", "M1"] if args.phase == "test1" else [args.winner]
        for arm in arms:
            flags = () if args.phase == "test1" else ("--atmosphere",)
            suffix = "" if args.phase == "test1" else "H"
            for size in ["1920x1080", "1280x720"]:
                for view in ["wide", "clinic", "traveler"]:
                    records.append(run(arm, view, size, suffix=suffix, options=flags))
            for diagnostic, extra in [("dry", "--dry"), ("no-wind", "--no-wind")]:
                records.append(run(arm, "wide", "1920x1080", suffix=suffix + "-" + diagnostic,
                                   options=(*flags, extra)))
    elif args.phase == "motion":
        for arm, suffix, flags in [("A0", "", ()), ("A1", "", ()), ("G1", "", ()),
                                   ("M1", "", ()), (args.winner, "H", ("--atmosphere",))]:
            for movie, view in [("orbit", "wide"), ("weather", "clinic"), ("zoom", "traveler")]:
                records.append(run(arm, view, "1280x720", suffix=suffix + "-" + movie,
                                   options=flags, movie=movie, fps=args.fps))
    else:
        for pan in [0, 64]:
            records.append(run("G1", "clinic", "1920x1080", suffix=f"-anchor-{pan}",
                               options=("--pigment-debug", "--dry", "--no-wind",
                                        "--no-reflections", f"--pan={pan}")))
    sources = [ROOT / "prototype" / name for name in ["mock_scene.gd", "style_study.gd",
               "style_study.tscn", "assets/forest-clinic.glb", "assets/forest-clinic-prepared.glb",
               "tools/prepare_style_kit.py", "tools/capture_style_study.py"]]
    sources += list((ROOT / "prototype/shaders").glob("study_*"))
    if args.phase.startswith("painted"):
        sources += [ROOT / "prototype" / name for name in ["painted_pass.gd",
                    "tools/build_painted_crowns.py", "assets/painted-crowns.png",
                    "assets/painted-crowns.json", "assets/painted-boughs-source.png"]]
    provenance = {"phase": args.phase, "captures": records,
                  "sources": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in sources},
                  "provenance": "Untouched Godot output. Procedural Blender stand-in, not AI-generated geometry. Software renderer; no target hardware performance claim."}
    if args.phase.startswith("painted"):
        provenance["texture_provenance"] = "I1 uses an AI-generated gouache bough texture (gpt-image-2.5-flare), not an AI scene paint-over. Its committed source is chroma-keyed and recolored deterministically."
    (OUTPUT / f"{args.phase}-provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")


if __name__ == "__main__":
    main()
