#!/usr/bin/env python3
"""Import exact, user-approved reference PNGs from the handoff ZIP.

Safe: validates ZIP paths and SHA-256; never overwrites different existing images;
does not touch app code, git state, branches, or network. Python stdlib only.
Run: python scripts/import_approved_references.py [path/to/JAIME_HQ_REFERENCIAS_Y_HANDOFF.zip]
"""
from __future__ import annotations

import hashlib
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "JAIME_HQ_REFERENCIAS_Y_HANDOFF.zip"
DEST = ROOT / "assets" / "reference_images"
IMAGES = {
    "JAIME_HQ_SIMS_VIDEOWALL_APROBADA.png":
        "4e07c5f1ea91b598ce8e3fcbcc1e73da6332b64006f8c03a21df7fa7a515ef92",
    "JAIME_HQ_SIMS_BASE.png":
        "69101f7a18a0d48908b3e3a060e64ffeb1c89a2a975ccb085ac9bdf6dfd83347",
}


def main() -> int:
    source = Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) > 1 else DEFAULT
    if not source.is_file():
        print(f"NO DISPONIBLE: ZIP no encontrado en {source}")
        print("Coloca el ZIP original en la raíz del proyecto o indica su ruta.")
        return 2
    staged: list[tuple[Path, bytes]] = []
    with zipfile.ZipFile(source) as archive:
        for filename, expected in IMAGES.items():
            member = f"assets/reference_images/{filename}"
            try:
                info = archive.getinfo(member)
            except KeyError:
                print(f"ERROR: falta {member} en el ZIP.")
                return 3
            if info.file_size > 10_000_000:
                print(f"ERROR: imagen demasiado grande: {member}")
                return 3
            content = archive.read(info)
            actual = hashlib.sha256(content).hexdigest()
            if actual != expected:
                print(f"ERROR: SHA-256 incorrecto para {filename}: {actual}")
                return 4
            target = DEST / filename
            if target.exists():
                current = hashlib.sha256(target.read_bytes()).hexdigest()
                if current != expected:
                    print(f"ERROR: {target} ya existe con bytes diferentes. NO se sobrescribe.")
                    return 5
                print(f"YA EXISTE Y VERIFICADO: {target.relative_to(ROOT)}")
            else:
                staged.append((target, content))
    DEST.mkdir(parents=True, exist_ok=True)
    for target, content in staged:
        target.write_bytes(content)
        print(f"IMPORTADO Y VERIFICADO: {target.relative_to(ROOT)}")
    print("OK: los dos PNG originales están presentes con hash correcto.")
    print("Codex: revisa git status y añade SOLO los PNG verificados al commit adecuado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
