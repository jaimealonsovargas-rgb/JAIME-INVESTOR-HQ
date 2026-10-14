"""Descarga explícita de dos materiales CC0. No se ejecuta al arrancar la app."""
from pathlib import Path
import hashlib
import json
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "frontend/public/materials"
HEADERS = {"User-Agent": "JAIME-Investor-HQ/0.1 (local architecture prototype)", "Accept": "application/json"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=60) as response:
        return response.read()


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    manifest = []
    for asset in ["dark_wood", "marble_01"]:
        info = json.loads(get(f"https://api.polyhaven.com/info/{asset}"))
        files = json.loads(get(f"https://api.polyhaven.com/files/{asset}"))
        for channel in ["Diffuse", "nor_gl", "Rough"]:
            entry = files[channel]["1k"]["jpg"]
            data = get(entry["url"])
            if hashlib.md5(data).hexdigest() != entry["md5"]:
                raise RuntimeError("Hash del recurso no coincide")
            name = f"{asset}_{channel.lower()}.jpg"
            (DEST / name).write_bytes(data)
            manifest.append({"asset": asset, "channel": channel, "file": name,
                "url": entry["url"], "authors": info["authors"], "license": "CC0-1.0",
                "license_source": f"https://polyhaven.com/a/{asset}", "retrieved": "2026-10-13",
                "source_version": info["files_hash"], "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
    (ROOT / "assets/P1_ASSET_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"{len(manifest)} mapas CC0 verificados, {sum(m['bytes'] for m in manifest)} bytes.")


if __name__ == "__main__":
    main()
