"""Descarga explícita de fuentes CC0, sin software pesado ni red en runtime.

El ZIP de sistema se consulta por HTTP Range; no se descarga el pack completo.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'assets' / 'source-humans'
CORE_COMMIT = 'a8bc2d54ff0ac92e78ff71431b1023eda42bf482'
CORE = f'https://raw.githubusercontent.com/makehumancommunity/makehuman/{CORE_COMMIT}/'
PACK_ROOT = 'https://files.makehumancommunity.org/asset_packs/'


class RemoteZip(io.RawIOBase):
    def __init__(self, url):
        self.url, self.position = url, 0
        with urllib.request.urlopen(urllib.request.Request(url, method='HEAD'), timeout=20) as r:
            self.size = int(r.headers['Content-Length'])
            self.etag = r.headers['ETag']

    def seekable(self): return True
    def readable(self): return True
    def tell(self): return self.position
    def seek(self, offset, whence=0):
        self.position = offset if whence == 0 else self.position + offset if whence == 1 else self.size + offset
        return self.position

    def read(self, size=-1):
        size = min(self.size-self.position, size if size >= 0 else self.size-self.position)
        if size <= 0: return b''
        request = urllib.request.Request(self.url, headers={'Range': f'bytes={self.position}-{self.position+size-1}', 'If-Range': self.etag})
        with urllib.request.urlopen(request, timeout=30) as r:
            if r.status != 206 or r.headers.get('ETag') != self.etag:
                raise RuntimeError('Servidor no permite Range consistente; descarga detenida.')
            data = r.read(size+1)
        if len(data) != size: raise RuntimeError('Range incompleto')
        self.position += size
        return data


def pack(name):
    return zipfile.ZipFile(RemoteZip(f'{PACK_ROOT}{name}/{name}_cc0.zip'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['inspect', 'core', 'assets'])
    args = parser.parse_args()
    if args.command == 'inspect':
        for name in ['suits01', 'makehuman_system_assets']:
            z = pack(name)
            relevant = [n for n in z.namelist() if any(k in n.lower() for k in ['male_suit_tie', 'young_lightskinned', 'short02', 'shoes01', 'eyes', 'license'])]
            print(name, '\n' + '\n'.join(relevant[:90]))
        return
    if args.command == 'assets':
        manifest = json.loads((SOURCE / 'SOURCE_MANIFEST.json').read_text(encoding='utf-8'))
        selected = {
            'suits01': ['clothes/toigo_male_suit_tie_and_jacket/'],
            'makehuman_system_assets': ['clothes/shoes01/', 'hair/short02/', 'eyes/low-poly/', 'eyes/materials/brown.mhmat', 'eyes/materials/brown_eye.png', 'skins/young_caucasian_male/'],
        }
        for name, prefixes in selected.items():
            z = pack(name)
            for path in z.namelist():
                if path.endswith('/') or not any(path.startswith(prefix) for prefix in prefixes): continue
                target = (SOURCE / path).resolve()
                if not target.is_relative_to(SOURCE.resolve()): raise RuntimeError('Ruta ZIP fuera de fuentes')
                data = z.read(path)
                target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)
                manifest.append(dict(file=path, url=f'{PACK_ROOT}{name}/{name}_cc0.zip#{path}', license='CC0-1.0', license_source=f'https://static.makehumancommunity.org/assets/assetpacks/{name}.html', sha256=hashlib.sha256(data).hexdigest(), bytes=len(data)))
        (SOURCE / 'SOURCE_MANIFEST.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        print('Fuentes seleccionadas:', len(manifest), 'archivos; sin descargar el pack completo')
        return
    paths = ['LICENSE.ASSETS.md', 'LICENSE.md', 'makehuman/data/3dobjs/base.obj', 'makehuman/data/rigs/default.mhskel', 'makehuman/data/rigs/default_weights.mhw']
    SOURCE.mkdir(parents=True, exist_ok=True)
    manifest = []
    for path in paths:
        url = CORE + path
        data = urllib.request.urlopen(url, timeout=30).read()
        target = SOURCE / Path(path).name
        target.write_bytes(data)
        notice='Legal notice: code AGPL-3.0 / graphical assets CC0-1.0' if target.name=='LICENSE.md' else 'CC0-1.0 graphical assets legal notice' if target.name=='LICENSE.ASSETS.md' else 'CC0-1.0 (core graphical assets)'
        manifest.append(dict(file=target.name, url=url, version=CORE_COMMIT, license=notice, bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
    (SOURCE / 'SOURCE_MANIFEST.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print('Fuentes núcleo descargadas:', len(manifest))


if __name__ == '__main__': main()
