# Licencias y dependencias P0

Verificación: 2026-10-13. Inventario generado por `scripts/license_inventory.py` desde los paquetes instalados y el lockfile npm. Incluye herramientas de desarrollo/auditoría y dependencias transitivas; no implica haber conectado proveedores financieros.

## Entorno y uso local

- Node 26.3.0: [MIT y avisos de terceros](https://github.com/nodejs/node/blob/v26.3.0/LICENSE).
- Python 3.14.4: [PSF-2.0 y licencias incorporadas](https://docs.python.org/3.14/license.html).
- SQLite: [dominio público](https://sqlite.org/copyright.html). Versión efectiva registrada en STATUS.md.
- uv 0.13.0 (bootstrap en .tools): [MIT o Apache-2.0](https://pypi.org/project/uv/0.13.0/).
- Playwright CLI: herramienta de verificación externa al producto, [Apache-2.0](https://github.com/microsoft/playwright-cli). No es dependencia de ejecución.
- Fuentes: pila del sistema; no se redistribuyen archivos tipográficos. Icono J: SVG propio. Sin assets 3D ni imágenes externas en P0.
- Uso local de las dependencias sin suscripción ni licencia de pago obligatoria. Mantener los avisos de terceros si se redistribuyen sus binarios. MPL-2.0 de certifi se conserva en su paquete; no se ha modificado.

## Python

Fuente: METADATA/LICENSE de cada wheel descargado de PyPI. Versiones y hashes fijados en uv.lock.

| Paquete | Versión | Licencia declarada/verificada |
|---|---|---|
| [alembic](https://pypi.org/project/alembic/1.20.0/) | 1.20.0 | MIT |
| [annotated-doc](https://pypi.org/project/annotated-doc/0.0.5/) | 0.0.5 | MIT |
| [annotated-types](https://pypi.org/project/annotated-types/0.8.0/) | 0.8.0 | MIT |
| [anyio](https://pypi.org/project/anyio/4.15.1/) | 4.15.1 | MIT |
| [boolean.py](https://pypi.org/project/boolean.py/5.0/) | 5.0 | BSD-2-Clause |
| [CacheControl](https://pypi.org/project/CacheControl/0.14.4/) | 0.14.4 | Apache-2.0 |
| [certifi](https://pypi.org/project/certifi/2026.7.22/) | 2026.7.22 | MPL-2.0 |
| [charset-normalizer](https://pypi.org/project/charset-normalizer/3.5.2/) | 3.5.2 | MIT |
| [click](https://pypi.org/project/click/8.5.0/) | 8.5.0 | BSD-3-Clause |
| [colorama](https://pypi.org/project/colorama/0.4.6/) | 0.4.6 | BSD-3-Clause |
| [cyclonedx-python-lib](https://pypi.org/project/cyclonedx-python-lib/11.12.0/) | 11.12.0 | Apache-2.0 |
| [defusedxml](https://pypi.org/project/defusedxml/0.7.1/) | 0.7.1 | PSFL |
| [fastapi](https://pypi.org/project/fastapi/0.143.0/) | 0.143.0 | MIT |
| [filelock](https://pypi.org/project/filelock/4.1.1/) | 4.1.1 | MIT |
| [h11](https://pypi.org/project/h11/0.16.0/) | 0.16.0 | MIT |
| [httpcore](https://pypi.org/project/httpcore/1.0.9/) | 1.0.9 | BSD-3-Clause |
| [httpx](https://pypi.org/project/httpx/0.28.1/) | 0.28.1 | BSD-3-Clause |
| [idna](https://pypi.org/project/idna/3.20/) | 3.20 | BSD-3-Clause |
| [iniconfig](https://pypi.org/project/iniconfig/2.3.1/) | 2.3.1 | MIT |
| [license-expression](https://pypi.org/project/license-expression/30.4.4/) | 30.4.4 | Apache-2.0 |
| [Mako](https://pypi.org/project/Mako/1.4.3/) | 1.4.3 | MIT |
| [markdown-it-py](https://pypi.org/project/markdown-it-py/4.2.0/) | 4.2.0 | MIT License |
| [MarkupSafe](https://pypi.org/project/MarkupSafe/3.0.4/) | 3.0.4 | BSD-3-Clause |
| [mdurl](https://pypi.org/project/mdurl/0.1.2/) | 0.1.2 | MIT License |
| [msgpack](https://pypi.org/project/msgpack/1.2.3/) | 1.2.3 | Apache-2.0 |
| [opentelemetry-api](https://pypi.org/project/opentelemetry-api/1.45.1/) | 1.45.1 | Apache-2.0 |
| [packageurl-python](https://pypi.org/project/packageurl-python/0.17.6/) | 0.17.6 | MIT |
| [packaging](https://pypi.org/project/packaging/26.3/) | 26.3 | Apache-2.0 OR BSD-2-Clause |
| [pip](https://pypi.org/project/pip/26.2.1/) | 26.2.1 | MIT |
| [pip-requirements-parser](https://pypi.org/project/pip-requirements-parser/32.0.1/) | 32.0.1 | MIT |
| [pip_api](https://pypi.org/project/pip_api/0.0.35/) | 0.0.35 | Apache-2.0 |
| [pip_audit](https://pypi.org/project/pip_audit/2.10.1/) | 2.10.1 | Apache-2.0 |
| [platformdirs](https://pypi.org/project/platformdirs/4.13.0/) | 4.13.0 | MIT |
| [pluggy](https://pypi.org/project/pluggy/1.6.0/) | 1.6.0 | MIT |
| [py-serializable](https://pypi.org/project/py-serializable/2.1.0/) | 2.1.0 | Apache-2.0 |
| [pydantic](https://pypi.org/project/pydantic/2.14.1/) | 2.14.1 | MIT |
| [pydantic-settings](https://pypi.org/project/pydantic-settings/2.15.0/) | 2.15.0 | MIT |
| [pydantic_core](https://pypi.org/project/pydantic_core/2.50.1/) | 2.50.1 | MIT |
| [Pygments](https://pypi.org/project/Pygments/2.21.0/) | 2.21.0 | BSD-2-Clause |
| [pyparsing](https://pypi.org/project/pyparsing/3.3.3/) | 3.3.3 | MIT |
| [pytest](https://pypi.org/project/pytest/9.1.1/) | 9.1.1 | MIT |
| [python-dotenv](https://pypi.org/project/python-dotenv/1.2.4/) | 1.2.4 | BSD-3-Clause |
| [requests](https://pypi.org/project/requests/2.34.2/) | 2.34.2 | Apache-2.0 |
| [rich](https://pypi.org/project/rich/15.0.0/) | 15.0.0 | MIT |
| [sortedcontainers](https://pypi.org/project/sortedcontainers/2.4.0/) | 2.4.0 | Apache-2.0 |
| [SQLAlchemy](https://pypi.org/project/SQLAlchemy/2.1.4/) | 2.1.4 | MIT |
| [starlette](https://pypi.org/project/starlette/1.8.0/) | 1.8.0 | BSD-3-Clause |
| [tomli](https://pypi.org/project/tomli/2.5.0/) | 2.5.0 | MIT |
| [tomli_w](https://pypi.org/project/tomli_w/1.2.0/) | 1.2.0 | MIT License |
| [typing-inspection](https://pypi.org/project/typing-inspection/0.4.4/) | 0.4.4 | MIT |
| [typing_extensions](https://pypi.org/project/typing_extensions/4.16.0/) | 4.16.0 | PSF-2.0 |
| [urllib3](https://pypi.org/project/urllib3/2.8.0/) | 2.8.0 | MIT |
| [uvicorn](https://pypi.org/project/uvicorn/0.54.0/) | 0.54.0 | BSD-3-Clause |

## npm

Fuente: campos license/resolved/integrity de package-lock.json publicados por los paquetes. Incluye variantes opcionales por plataforma, aunque no se instalen en Windows.

| Paquete | Versión | Licencia declarada |
|---|---|---|
| [@jridgewell/resolve-uri](https://www.npmjs.com/package/@jridgewell/resolve-uri/v/3.1.2) | 3.1.2 | MIT |
| [@jridgewell/sourcemap-codec](https://www.npmjs.com/package/@jridgewell/sourcemap-codec/v/1.6.0) | 1.6.0 | MIT |
| [@jridgewell/trace-mapping](https://www.npmjs.com/package/@jridgewell/trace-mapping/v/0.3.31) | 0.3.31 | MIT |
| [@oxc-project/types](https://www.npmjs.com/package/@oxc-project/types/v/0.153.0) | 0.153.0 | MIT |
| [@rolldown/binding-android-arm-eabi](https://www.npmjs.com/package/@rolldown/binding-android-arm-eabi/v/1.2.13) | 1.2.13 | MIT |
| [@rolldown/binding-android-arm64](https://www.npmjs.com/package/@rolldown/binding-android-arm64/v/1.2.13) | 1.2.13 | MIT |
| [@rolldown/binding-darwin-arm64](https://www.npmjs.com/package/@rolldown/binding-darwin-arm64/v/1.2.13) | 1.2.13 | MIT |
| [@rolldown/binding-darwin-x64](https://www.npmjs.com/package/@rolldown/binding-darwin-x64/v/1.2.13) | 1.2.13 | MIT |
| [@rolldown/binding-freebsd-x64](https://www.npmjs.com/package/@rolldown/binding-freebsd-x64/v/1.2.13) | 1.2.13 | MIT |
| [@rolldown/binding-linux-arm-gnueabihf](https://www.npmjs.com/package/@rolldown/binding-linux-arm-gnueabihf/v/1.2.13) | 1.2.13 | MIT |
| [@rolldown/binding-linux-arm64-gnu](https://www.npmjs.com/package/@rolldown/binding-linux-arm64-gnu/v/1.2.13) | 1.2.13 | MIT |
| [@rolldown/binding-linux-arm64-musl](https://www.npmjs.com/package/@rolldown/binding-linux-arm64-musl/v/1.2.13) | 1.2.13 | MIT |
| [@rolldown/binding-linux-ppc64-gnu](https://www.npmjs.com/package/@rolldown/binding-linux-ppc64-gnu/v/1.2.13) | 1.2.13 | MIT |
| [@rolldown/binding-linux-s390x-gnu](https://www.npmjs.com/package/@rolldown/binding-linux-s390x-gnu/v/1.2.13) | 1.2.13 | MIT |
| [@rolldown/binding-linux-x64-gnu](https://www.npmjs.com/package/@rolldown/binding-linux-x64-gnu/v/1.2.13) | 1.2.13 | MIT |
| [@rolldown/binding-linux-x64-musl](https://www.npmjs.com/package/@rolldown/binding-linux-x64-musl/v/1.2.13) | 1.2.13 | MIT |
| [@rolldown/binding-openharmony-arm64](https://www.npmjs.com/package/@rolldown/binding-openharmony-arm64/v/1.2.13) | 1.2.13 | MIT |
| [@rolldown/binding-win32-arm64-msvc](https://www.npmjs.com/package/@rolldown/binding-win32-arm64-msvc/v/1.2.13) | 1.2.13 | MIT |
| [@rolldown/binding-win32-x64-msvc](https://www.npmjs.com/package/@rolldown/binding-win32-x64-msvc/v/1.2.13) | 1.2.13 | MIT |
| [@rolldown/pluginutils](https://www.npmjs.com/package/@rolldown/pluginutils/v/1.0.1) | 1.0.1 | MIT |
| [@tanstack/query-core](https://www.npmjs.com/package/@tanstack/query-core/v/5.104.2) | 5.104.2 | MIT |
| [@tanstack/react-query](https://www.npmjs.com/package/@tanstack/react-query/v/5.104.2) | 5.104.2 | MIT |
| [@types/chai](https://www.npmjs.com/package/@types/chai/v/5.2.3) | 5.2.3 | MIT |
| [@types/deep-eql](https://www.npmjs.com/package/@types/deep-eql/v/4.0.2) | 4.0.2 | MIT |
| [@types/estree](https://www.npmjs.com/package/@types/estree/v/1.0.9) | 1.0.9 | MIT |
| [@types/react](https://www.npmjs.com/package/@types/react/v/19.2.14) | 19.2.14 | MIT |
| [@types/react-dom](https://www.npmjs.com/package/@types/react-dom/v/19.2.3) | 19.2.3 | MIT |
| [@typescript/typescript-aix-ppc64](https://www.npmjs.com/package/@typescript/typescript-aix-ppc64/v/7.0.2) | 7.0.2 | Apache-2.0 |
| [@typescript/typescript-darwin-arm64](https://www.npmjs.com/package/@typescript/typescript-darwin-arm64/v/7.0.2) | 7.0.2 | Apache-2.0 |
| [@typescript/typescript-darwin-x64](https://www.npmjs.com/package/@typescript/typescript-darwin-x64/v/7.0.2) | 7.0.2 | Apache-2.0 |
| [@typescript/typescript-freebsd-arm64](https://www.npmjs.com/package/@typescript/typescript-freebsd-arm64/v/7.0.2) | 7.0.2 | Apache-2.0 |
| [@typescript/typescript-freebsd-x64](https://www.npmjs.com/package/@typescript/typescript-freebsd-x64/v/7.0.2) | 7.0.2 | Apache-2.0 |
| [@typescript/typescript-linux-arm](https://www.npmjs.com/package/@typescript/typescript-linux-arm/v/7.0.2) | 7.0.2 | Apache-2.0 |
| [@typescript/typescript-linux-arm64](https://www.npmjs.com/package/@typescript/typescript-linux-arm64/v/7.0.2) | 7.0.2 | Apache-2.0 |
| [@typescript/typescript-linux-loong64](https://www.npmjs.com/package/@typescript/typescript-linux-loong64/v/7.0.2) | 7.0.2 | Apache-2.0 |
| [@typescript/typescript-linux-mips64el](https://www.npmjs.com/package/@typescript/typescript-linux-mips64el/v/7.0.2) | 7.0.2 | Apache-2.0 |
| [@typescript/typescript-linux-ppc64](https://www.npmjs.com/package/@typescript/typescript-linux-ppc64/v/7.0.2) | 7.0.2 | Apache-2.0 |
| [@typescript/typescript-linux-riscv64](https://www.npmjs.com/package/@typescript/typescript-linux-riscv64/v/7.0.2) | 7.0.2 | Apache-2.0 |
| [@typescript/typescript-linux-s390x](https://www.npmjs.com/package/@typescript/typescript-linux-s390x/v/7.0.2) | 7.0.2 | Apache-2.0 |
| [@typescript/typescript-linux-x64](https://www.npmjs.com/package/@typescript/typescript-linux-x64/v/7.0.2) | 7.0.2 | Apache-2.0 |
| [@typescript/typescript-netbsd-arm64](https://www.npmjs.com/package/@typescript/typescript-netbsd-arm64/v/7.0.2) | 7.0.2 | Apache-2.0 |
| [@typescript/typescript-netbsd-x64](https://www.npmjs.com/package/@typescript/typescript-netbsd-x64/v/7.0.2) | 7.0.2 | Apache-2.0 |
| [@typescript/typescript-openbsd-arm64](https://www.npmjs.com/package/@typescript/typescript-openbsd-arm64/v/7.0.2) | 7.0.2 | Apache-2.0 |
| [@typescript/typescript-openbsd-x64](https://www.npmjs.com/package/@typescript/typescript-openbsd-x64/v/7.0.2) | 7.0.2 | Apache-2.0 |
| [@typescript/typescript-sunos-x64](https://www.npmjs.com/package/@typescript/typescript-sunos-x64/v/7.0.2) | 7.0.2 | Apache-2.0 |
| [@typescript/typescript-win32-arm64](https://www.npmjs.com/package/@typescript/typescript-win32-arm64/v/7.0.2) | 7.0.2 | Apache-2.0 |
| [@typescript/typescript-win32-x64](https://www.npmjs.com/package/@typescript/typescript-win32-x64/v/7.0.2) | 7.0.2 | Apache-2.0 |
| [@vitejs/plugin-react](https://www.npmjs.com/package/@vitejs/plugin-react/v/6.1.2) | 6.1.2 | MIT |
| [@vitest/mocker](https://www.npmjs.com/package/@vitest/mocker/v/5.0.4) | 5.0.4 | MIT |
| [@vitest/spy](https://www.npmjs.com/package/@vitest/spy/v/5.0.4) | 5.0.4 | MIT |
| [assertion-error](https://www.npmjs.com/package/assertion-error/v/2.0.1) | 2.0.1 | MIT |
| [chai](https://www.npmjs.com/package/chai/v/6.3.0) | 6.3.0 | MIT |
| [csstype](https://www.npmjs.com/package/csstype/v/3.2.3) | 3.2.3 | MIT |
| [detect-libc](https://www.npmjs.com/package/detect-libc/v/2.1.2) | 2.1.2 | Apache-2.0 |
| [es-module-lexer](https://www.npmjs.com/package/es-module-lexer/v/2.3.2) | 2.3.2 | MIT |
| [estree-walker](https://www.npmjs.com/package/estree-walker/v/3.0.3) | 3.0.3 | MIT |
| [expect-type](https://www.npmjs.com/package/expect-type/v/1.4.0) | 1.4.0 | Apache-2.0 |
| [fdir](https://www.npmjs.com/package/fdir/v/6.5.0) | 6.5.0 | MIT |
| [fsevents](https://www.npmjs.com/package/fsevents/v/2.3.3) | 2.3.3 | MIT |
| [lightningcss](https://www.npmjs.com/package/lightningcss/v/1.33.0) | 1.33.0 | MPL-2.0 |
| [lightningcss-android-arm64](https://www.npmjs.com/package/lightningcss-android-arm64/v/1.33.0) | 1.33.0 | MPL-2.0 |
| [lightningcss-darwin-arm64](https://www.npmjs.com/package/lightningcss-darwin-arm64/v/1.33.0) | 1.33.0 | MPL-2.0 |
| [lightningcss-darwin-x64](https://www.npmjs.com/package/lightningcss-darwin-x64/v/1.33.0) | 1.33.0 | MPL-2.0 |
| [lightningcss-freebsd-x64](https://www.npmjs.com/package/lightningcss-freebsd-x64/v/1.33.0) | 1.33.0 | MPL-2.0 |
| [lightningcss-linux-arm-gnueabihf](https://www.npmjs.com/package/lightningcss-linux-arm-gnueabihf/v/1.33.0) | 1.33.0 | MPL-2.0 |
| [lightningcss-linux-arm64-gnu](https://www.npmjs.com/package/lightningcss-linux-arm64-gnu/v/1.33.0) | 1.33.0 | MPL-2.0 |
| [lightningcss-linux-arm64-musl](https://www.npmjs.com/package/lightningcss-linux-arm64-musl/v/1.33.0) | 1.33.0 | MPL-2.0 |
| [lightningcss-linux-x64-gnu](https://www.npmjs.com/package/lightningcss-linux-x64-gnu/v/1.33.0) | 1.33.0 | MPL-2.0 |
| [lightningcss-linux-x64-musl](https://www.npmjs.com/package/lightningcss-linux-x64-musl/v/1.33.0) | 1.33.0 | MPL-2.0 |
| [lightningcss-win32-arm64-msvc](https://www.npmjs.com/package/lightningcss-win32-arm64-msvc/v/1.33.0) | 1.33.0 | MPL-2.0 |
| [lightningcss-win32-x64-msvc](https://www.npmjs.com/package/lightningcss-win32-x64-msvc/v/1.33.0) | 1.33.0 | MPL-2.0 |
| [magic-string](https://www.npmjs.com/package/magic-string/v/1.4.3) | 1.4.3 | MIT |
| [nanoid](https://www.npmjs.com/package/nanoid/v/3.3.20) | 3.3.20 | MIT |
| [obug](https://www.npmjs.com/package/obug/v/3.0.0) | 3.0.0 | MIT |
| [picocolors](https://www.npmjs.com/package/picocolors/v/1.1.1) | 1.1.1 | ISC |
| [picomatch](https://www.npmjs.com/package/picomatch/v/4.0.7) | 4.0.7 | MIT |
| [postcss](https://www.npmjs.com/package/postcss/v/8.5.30) | 8.5.30 | MIT |
| [react](https://www.npmjs.com/package/react/v/19.3.0) | 19.3.0 | MIT |
| [react-dom](https://www.npmjs.com/package/react-dom/v/19.3.0) | 19.3.0 | MIT |
| [rolldown](https://www.npmjs.com/package/rolldown/v/1.2.13) | 1.2.13 | MIT |
| [scheduler](https://www.npmjs.com/package/scheduler/v/0.28.0) | 0.28.0 | MIT |
| [source-map-js](https://www.npmjs.com/package/source-map-js/v/1.2.2) | 1.2.2 | BSD-3-Clause |
| [std-env](https://www.npmjs.com/package/std-env/v/4.3.0) | 4.3.0 | MIT |
| [tinybench](https://www.npmjs.com/package/tinybench/v/6.2.2) | 6.2.2 | MIT |
| [tinyexec](https://www.npmjs.com/package/tinyexec/v/1.3.1) | 1.3.1 | MIT |
| [tinyglobby](https://www.npmjs.com/package/tinyglobby/v/0.2.17) | 0.2.17 | MIT |
| [typescript](https://www.npmjs.com/package/typescript/v/7.0.2) | 7.0.2 | Apache-2.0 |
| [vite](https://www.npmjs.com/package/vite/v/8.3.4) | 8.3.4 | MIT |
| [vitest](https://www.npmjs.com/package/vitest/v/5.0.4) | 5.0.4 | MIT |
| [why-is-node-running](https://www.npmjs.com/package/why-is-node-running/v/3.2.1) | 3.2.1 | MIT |

## Fuentes técnicas consultadas

- [Requisitos de Vite](https://vite.dev/guide/): runtime compatible; probado en el Node instalado.
- [FastAPI local](https://fastapi.tiangolo.com/deployment/manually/), [SQLite/SQLAlchemy](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html), [lock y sincronización uv](https://docs.astral.sh/uv/concepts/projects/sync/).
- [Alpaca Paper](https://docs.alpaca.markets/us/docs/paper-trading) y [Trading 212](https://docs.trading212.com/api): solo validación documental de hosts. Acceso, cuotas, cobertura y derechos de datos NO comprobados; proveedores NO DISPONIBLES en P0.
