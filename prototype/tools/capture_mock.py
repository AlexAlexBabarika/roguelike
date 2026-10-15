"""Capture the three mock cameras and fingerprint their inputs; stdlib only."""

import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess


ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "prototype"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command):
    result = subprocess.run(
        command, cwd=ROOT, capture_output=True, text=True, timeout=120, check=False
    )
    log = result.stdout + result.stderr
    print(log, end="")
    result.check_returncode()
    if "SCRIPT ERROR:" in log or "\nERROR:" in log:
        raise RuntimeError("Godot reported an error")
    return log


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--godot", default="godot")
    parser.add_argument("--xvfb", action="store_true", help="Linux displayless OpenGL")
    parser.add_argument("--output", type=Path, default=ROOT / "docs/screenshots/forest-clinic")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    run([args.godot, "--headless", "--editor", "--import", "--path", str(PROJECT)])
    prefix = ["xvfb-run", "-a", "-s", "-screen 0 1920x1080x24"] if args.xvfb else []
    records = []
    for view in ("wide", "clinic", "traveler"):
        path = output / f"{view}.png"
        log = run(prefix + [
            args.godot, "--audio-driver", "Dummy", "--path", str(PROJECT),
            "--resolution", "1920x1080", "res://mock_scene.tscn", "--",
            f"--view={view}", f"--capture={path}",
        ])
        data = path.read_bytes()
        if data[:8] != b"\x89PNG\r\n\x1a\n" or struct.unpack(">II", data[16:24]) != (1920, 1080):
            raise RuntimeError(f"Invalid capture size or format: {path}")
        settings = json.loads(next(line.removeprefix("MOCK_VIEW: ")
                                   for line in log.splitlines() if line.startswith("MOCK_VIEW: ")))
        records.append({
            "path": path.name,
            "kind": "Godot capture",
            "sha256": sha256(path),
            "settings": settings,
            "driver": next(line for line in log.splitlines() if line.startswith("OpenGL API")),
        })
    sources = [
        PROJECT / "project.godot", PROJECT / "mock_scene.tscn", PROJECT / "mock_scene.gd",
        PROJECT / "assets/forest-clinic.glb", PROJECT / "assets/forest-clinic.json",
        PROJECT / "tools/build_mock_scene.py", Path(__file__).resolve(),
        *sorted((PROJECT / "shaders").glob("mock_*.gdshader")),
    ]
    provenance = {
        "description": "Untouched Godot engine PNGs; no AI image, overpaint or compositing.",
        "renderer": "Compatibility / OpenGL",
        "msaa_samples": 4,
        "seed": 40217,
        "capture_settle_frames": 20,
        "sources": [{"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}
                    for path in sources],
        "captures": records,
        "limitations": "Static art study; no gameplay, animation or hardware performance validation.",
    }
    (output / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(f"MOCK_ARCHIVE: {output}")


if __name__ == "__main__":
    main()
