"""Capture actual Godot viewports; no paint-over, filter, crop or image synthesis."""

import argparse
import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]
SHOTS = {
    'daylight': ['--view=wide'],
    'tree': ['--view=tree', '--isolated'],
    'silhouette': ['--view=tree', '--silhouette'],
    'approach': ['--view=grove'],
    'weather': ['--view=wide', '--weather'],
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--godot', default=os.environ.get('GODOT', 'godot'))
    args = parser.parse_args()
    target = ROOT / 'docs/screenshots/clinic-grove'
    target.mkdir(exist_ok=True)
    for name, options in SHOTS.items():
        path = target / (name + '.png')
        command = ['xvfb-run', '-a', args.godot, '--audio-driver', 'Dummy', '--disable-vsync',
                   '--resolution', '1280x800', '--path', str(ROOT / 'prototype'),
                   'res://clinic_grove.tscn', '--', '--no-wind', '--capture=' + str(path)] + options
        result = subprocess.run(command, text=True, capture_output=True, timeout=150, check=True)
        output = result.stdout + result.stderr
        print(output, flush=True)
        if any(error in output for error in ['SCRIPT ERROR:', 'SHADER ERROR:', '\nERROR:']):
            raise RuntimeError('Godot reported errors during ' + name)
        if not path.exists() or not path.with_suffix('.json').exists():
            raise RuntimeError('Missing image or provenance: ' + name)


if __name__ == '__main__':
    main()
