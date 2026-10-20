# Corrección TLS — 20-10-2026

La auditoría actual encontró `certifi 2026.7.22` afectado por [GHSA-6q48-6c7w-9gw2](https://github.com/advisories/GHSA-6q48-6c7w-9gw2), publicado hoy. La biblioteca incluía autoridades raíz afectadas por claves intermedias comprometidas.

Se actualizó únicamente certifi a **2026.10.19** con `uv lock --upgrade-package certifi==2026.10.19 --no-python-downloads` y `uv sync --locked --no-python-downloads`. El lock conserva hashes de los artefactos; ningún otro paquete cambió. No se desactiva TLS ni se aceptan certificados inválidos.

Repetición real de `python scripts/manage.py audit`: exit 0; Python sin vulnerabilidades conocidas y npm con cero vulnerabilidades. Log negativo y positivo preservados en `output/p4-data-refresh/audit-p49*.txt`.
