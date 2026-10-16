"""Fetch pinned CC0 source files; checked-in runtime assets need no network.

python3 prototype/tools/fetch_reference_forest.py --cache /absolute/cache
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import urllib.request

from PIL import Image


ASSETS = Path(__file__).resolve().parents[1] / 'assets' / 'reference-forest'
HEADERS = {'User-Agent': 'RoguelikeLookdev/1.0', 'Referer': 'https://polyhaven.com/'}
MODELS = ['fir_tree_01', 'rock_moss_set_01', 'fern_02']
SURFACES = ['forest_floor', 'forrest_ground_01', 'mossy_rock', 'weathered_planks', 'rusty_metal_sheet']


def request(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=180)


def leaves(value):
    if not isinstance(value, dict):
        return
    if 'url' in value and 'md5' in value:
        yield value
    for item in value.values():
        yield from leaves(item)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, required=True)
    args = parser.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(exist_ok=True)
    sources, jobs, maps = [], [], []
    manifest = ASSETS / 'sources.json'
    pinned = {item['id']: item for item in json.loads(manifest.read_text())['sources']} if manifest.exists() else {}
    for asset in MODELS + SURFACES:
        if asset in pinned:
            files = {str(index): item for index, item in enumerate(pinned[asset]['files'])}
            info = pinned[asset]
        else:
            with request('https://api.polyhaven.com/files/' + asset) as response:
                files = json.load(response)
            with request('https://api.polyhaven.com/info/' + asset) as response:
                info = json.load(response)
        source = {'id': asset, 'url': 'https://polyhaven.com/a/' + asset,
                  'authors': info['authors'], 'license': 'CC0-1.0',
                  'license_url': 'https://polyhaven.com/license', 'files': []}
        choices = list(leaves(files))
        names = []
        if asset in MODELS:
            names.append(asset + '_1k.blend')
        if asset == 'fir_tree_01':
            for part in ['bark', 'trunk_a', 'trunk_b', 'trunk_c', 'twig']:
                for channel in ['diff', 'nor_gl']:
                    names.append(f'{asset}_{part}_{channel}_1k.png')
            names.append(asset + '_twig_alpha_1k.png')
        else:
            for channel in ['diff', 'nor_gl']:
                names.append(f'{asset}_{channel}_1k.jpg')
            if asset == 'fern_02':
                names.append(asset + '_alpha_1k.png')
        for name in names:
            entry = next(item for item in choices if item['url'].endswith('/' + name))
            local = args.cache / name
            # Reuse the earlier source layout without downloading duplicate maps.
            if (args.cache / 'textures' / name).is_file():
                local = args.cache / 'textures' / name
            jobs.append((local, entry))
            source['files'].append({key: entry[key] for key in ['url', 'md5', 'size']})
            if not name.endswith('.blend'):
                maps.append((local, asset))
        sources.append(source)

    def fetch(job):
        local, entry = job
        if not local.is_file() or hashlib.md5(local.read_bytes()).hexdigest() != entry['md5']:
            with request(entry['url']) as response, local.open('wb') as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
        if hashlib.md5(local.read_bytes()).hexdigest() != entry['md5']:
            raise ValueError('Source checksum mismatch: ' + str(local))
        print('VERIFIED', local.name, flush=True)

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(fetch, jobs))
    for local, asset in maps:
        if '_alpha_' in local.name:
            continue
        image = Image.open(local).convert('RGB')
        image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        name = local.name.replace('_1k', '')
        if '_twig_diff_' in local.name or (asset == 'fern_02' and '_diff_' in local.name):
            alpha_file = next(p for p, _ in jobs if p.name == (
                asset + ('_twig_alpha_1k.png' if asset == 'fir_tree_01' else '_alpha_1k.png')))
            alpha = Image.open(alpha_file).convert('L').resize(image.size, Image.Resampling.LANCZOS)
            image.putalpha(alpha)
            image.save(ASSETS / Path(name).with_suffix('.png'))
        else:
            image.save(ASSETS / Path(name).with_suffix('.jpg'), quality=91, subsampling=0)
    record = {'license': 'CC0-1.0', 'sources': sources,
              'adaptations': ['Use artist-authored LOD2 conifers, not the multi-million-triangle LOD0.',
                              'Restore corner UVMap attributes as exportable UV coordinates.',
                              'Resize runtime maps to at most 1024px; combine foliage color/alpha.',
                              'External textures and ordinary lit alpha-scissor materials in Godot.'],
              'runtime_files': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in sorted(ASSETS.glob('*')) if p.suffix in ['.jpg', '.png']}}
    (ASSETS / 'sources.json').write_text(json.dumps(record, indent=2) + '\n')


if __name__ == '__main__':
    main()
