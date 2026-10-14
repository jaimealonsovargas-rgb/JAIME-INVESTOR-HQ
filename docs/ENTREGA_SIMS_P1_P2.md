# Entrega local JAIME INVESTOR HQ · P1 Sims + P2

2026-10-15. Alcance ejecutado: P1.S0–S4 y P2.0–P2.6 viable, gratuito y verificable. **STOP antes de P3.** El objetivo 45–60 FPS es parcial; proveedores condicionados y terceros inseguros permanecen bloqueados, no se presentan como integraciones completas.

## 1. Estado recibido

Oficina Three.js/R3F, mobiliario/PBR/humano CC0, navegación/colisiones/paneles P1 y protecciones P0 existentes. Corrección anterior con diez NPC y cuello de rendimiento; infraestructura P2, 32 adaptadores y Data Quality preparado sin montar. Se conservaron todos los commits y cambios locales; no se reconstruyó el proyecto.

## 2. Implementación realizada

Sims marfil/roble/azul noche sobre los mismos builders: distribución definitiva, Recepción sin sofás con operador detrás del mostrador, Performance accesible, Sistemas con dos puestos y racks, muros cutaway, ventanas, skyline y luces/materiales afinados. Cámara elevada fija y seguimiento amortiguado, solo flechas screen-relative, avatar completo y giro automático. **16 NPC sentados**, nueve principales y siete secundarios, animaciones ambientales y 17 rigs independientes.

Videowall físico enorme 32×4,8 m con **nueve módulos** y diálogo DOM accesible. Resumen local sin consultas externas por frame, datos autorizados o NO DISPONIBLE. Caché de poses/matrices, LOD y batching sin retirar personajes. P2 añade RSS BCE auditado, corrige USD/EUR, endurece XML/frescura/derechos/cache y monta Sistemas/Data Quality.

## 3. Funcionamiento comprobado

Recorrido continuo de nueve salas mediante flechas nativas, sin teleport ni escritura de pose; nueve paneles por proximidad a su NPC, sala/LOS, pausa, foco, Esc e histéresis. Flechas en cuatro direcciones, diagonales en recorrido, WASD/ratón ignorados. Dieciséis NPC sentados y nueve monitores conservados. Nueve módulos del videowall comprobados; DOM a 390 px sin overflow horizontal. Backend realmente detenido, sin mocks: ambos paneles NO DISPONIBLE y movimiento/foco recuperados. Diagnóstico P0 intacto.

## 4. Capturas auténticas

[Planta/videowall](evidencias/P1_SIMS/final-general.png) · [Recepción](evidencias/P1_SIMS/final-recepcion.png) · [Trading](evidencias/P1_SIMS/final-trading.png) · [Comité](evidencias/P1_SIMS/final-comite.png) · [Performance](evidencias/P1_SIMS/recorrido-performance.png) · [Sistemas](evidencias/P1_SIMS/final-sistemas.png) · [Centro de control](evidencias/P1_SIMS/videowall-referencia.png) · [Data Quality](evidencias/P2/sistemas-data-quality.png) · [Noticias](evidencias/P2/sistemas-noticias.png).

Las imágenes originales del usuario están versionadas en a3547bc con ambos SHA-256 verificados, tras localizarlas en Downloads/assets. **Son conceptos, no capturas de app.** El acabado es estilizado, no una reproducción pixel a pixel de la referencia. [Galería/evidencias](evidencias/P1_SIMS/README.md).

## 5. Rendimiento medido

Chrome/Windows, Intel Graphics 0xA7AC/D3D11, viewport 1920×1080, Equilibrado **DPR 0,8**, buffer 1536×864, MSAA y sombras 1024. Avatar moviéndose, 16 NPC/videowall activos; ventanas de 12 s y muestras móviles separadas de pausas. Sin tests/build/smokes concurrentes.

| Escenario | Media móvil FPS | Peor ventana móvil de 5 s | p95 ms |
|---|---:|---:|---:|
| Recepción | 36,38 | 32,73 | 62,2 |
| Trading | 46,60 | 43,75 | 42,5 |
| Comité | 41,69 | 38,92 | 49,6 |
| Sistemas | 46,13 | 43,34 | 37,6 |
| Pasillo | 40,76 | 36,97 | 53,6 |
| Recorrido/panel | 40,93 | 40,15 | 49,4 |

El mínimo se cumple en esas ventanas, **no en cada frame**; hay tirones. Objetivo 45–60 no alcanzado en todas las salas; Detalle no certificado. Se conserva el negativo DPR 0,85: Recepción 31,74 de media/28,79 en 5 s; se corrigió el perfil sin retirar contenido. Baseline previo diez NPC/Trading/DPR 1: 31,29, no comparación controlada. [Método, muestras y draw calls](evidencias/P1_SIMS/README.md); resumen reproducible con `python scripts/summarize_sims_fps.py`.

## 6. Proveedores realmente conectados

**31 candidatos, 35 modalidades, 33 adaptadores/29 proveedores implementados; 18 modalidades HTTP reales/17 proveedores.** Verificados: BCE (FX+RSS), BdE, INE, Eurostat, OCDE, Banco Mundial, BIS, Treasury, BLS v1, FMI DataMapper, ESMA índice FIRDS, Kraken, Binance data-only, CoinPaprika, CoinGecko público, Coinbase y OpenFIGI público.

Lectura local 23:37:33 UTC: **12 fuentes frescas utilizables/11 proveedores**, 98 instrumentos/series reales. Frescura caduca: conexión histórica no significa disponibilidad actual. Son presets acotados, no cobertura de todo el mercado. [Matriz reproducible de 35 modalidades](P2_PROVIDERS_VERIFICACION.md), [smokes y panel real](evidencias/P2/README.md).

## 7. Bloqueos y pendientes

**13 modalidades NO_CREDENTIALS**, sin cuentas creadas. SEC necesita contacto real; GDELT timeout en tres intentos acotados. Finnhub/Nasdaq: endpoint gratuito útil/derechos no confirmados, sin adaptador contado. **Cuatro restricciones display**: ESMA, Kraken, Binance y CoinGecko público. Coinbase/CoinPaprika tuvieron HTTP válido, pero precios caducados no cuentan como utilizables. ESMA solo índice de archivos, sin descarga masiva. Sin claves no se promete cobertura amplia de acciones/ETF/bonos individuales; sin identificador/divisa verificable no se inventa identidad ni compatibilidad paper. Investigación especializada adicional no se contabiliza como conexión.

## 8. Agent Reach / Vibe / Liquid

Agent Reach 1.5.0 MIT: fuente fijada, entorno aislado, safe/dry-run/safe/doctor limitado a RSS 1/1; sin cookies ni config personal. Integración operativa **solo RSS público BCE**, cinco noticias reales con fuente/fecha/autor cuando disponible/idioma; contenido no confiable nunca instrucciones. No se anuncian otros canales conectados.

Vibe 0.1.16 MIT/NOTICE: **30 presets YAML** verificados/hash, METADATA_ONLY/desactivados; benchmark de 1.000 parseos en 1,762 s, **no backtest**. Contrato de datos reales y 30 roles declarativos preparados, sin agentes/jobs/modelos/tools de trading. Subconjunto instalado auditado; runtime completo no instalado ni certificado. 6–10 equipos operativos pendientes P4/P5 y sandbox.

Liquid: **BLOCKED_TRADE_SCOPE / NO_PUBLIC_READ_ONLY_API_CONFIRMED**; OAuth estándar read+trade no conectado, sin MCP/wallet/cuenta. [Pins, permisos, licencias, SBOM y evidencias](INTEGRACIONES_TERCEROS_VERIFICACION.md).

## 9. Pruebas y seguridad

`python scripts/manage.py check`: **115 pytest + 35 Vitest, TypeScript/build correctos, salida 0**. Contratos/parsers/cache/cuotas/errores/SSRF/secretos/POST allowlisted/migraciones/P0/HQ incluidos. Audit Python sin vulnerabilidades conocidas/npm 0, salida 0. `git diff --check` y diff completo desde ab830a5, salida 0. Assets/FK/hashes y blobs de licencias/referencias verificados offline. Se conservan fallos y correcciones, incluido timeout del fixture de geometría (5,35 s sobre 5 s), corregido con presupuesto de 15 s y cámara isométrica actual.

Health 200/PAPER_ONLY/orders false/schema 0002_data; POST local LIVE negativo **403**. Ninguna orden externa ni sesión de broker, no ledger/cartera/NAV/jobs inventados. Secretos solo .env local. Coste adicional servicios **0 EUR**. XML con entidades/DTD o bytes nulos rechazado, cache de derechos actuales y datos mezclados caducados marcados STALE. [Logs y códigos](evidencias/P1_SIMS/comandos-entrega.json), [seguridad API](evidencias/P2/seguridad-y-calidad-entrega.json).

## 10. Commits y preservación

Backups y merges documentales seguros en STATUS, sin reset/clean/force/push. Commit de referencias **a3547bc**; cierre por bloques **70b2e52** (RSS/auditorías/metadatos), **43f09a4** (Sims/S4/rendimiento), **4b5c58c** (Data Quality/QA offline). Commit documental posterior registra este informe/STATUS y comprobaciones de integridad. Todo local, sin publicar automáticamente en GitHub.

## 11. Límites y deuda técnica

45–60 FPS parcial, tirones y dependencia de carga/energía; una base humana reutilizada, luz/reflejos aproximados y skyline conceptual. Bundle 3D 959 kB minificado/257 kB gzip y aviso Starlette/httpx, no errores de build. Auditorías detectan vulnerabilidades conocidas, no garantizan ausencia total; Vibe completo no auditado. Licencias gráficas MakeHuman/Margaret Toigo/Poly Haven **CC0**, Three/meshoptimizer **MIT**; [registro](../assets/LICENSES.md). Conceptos del usuario no se usan como texturas runtime ni reciben falsa licencia CC0. Algunas fuentes son solo investigación/referencia, nunca precios ejecutables.

## 12. Preparado para fases posteriores y comprobación local

Registry/aliases/capacidades, observaciones Decimal/UTC/derechos, caches/cuotas y resumen read-only sirven de base a P3. El ledger MASTER de 10.000 EUR ficticios **no existe todavía**; deberá quedar separado de balances paper externos. Treinta roles y 30 presets son declaraciones futuras P4/P5, no 30 LLM simultáneos. Cartera/posiciones P3, agentes P4, riesgo/comité P5 y operaciones P6 permanecen NO DISPONIBLES.

En dos terminales: `python scripts/manage.py backend` y `python scripts/manage.py frontend`; abrir `http://127.0.0.1:5173/`. Flechas para caminar, acercarse al NPC abre el panel; Esc cierra. «Vista general» muestra toda la sede y «Ver centro de control» sus nueve módulos. Sistemas permite filtrar/consultar un preset; el resto no consulta proveedores automáticamente. `/?diagnostico=1` conserva P0. No configurar planes de pago ni secretos VITE_*. **Detenido antes de P3 para revisión del usuario.**
