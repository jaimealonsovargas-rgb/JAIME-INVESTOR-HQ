# Cierre acotado P2 + P4 — PARTIAL, 22-10-2026

El usuario solicita detener iteraciones indefinidas y entregar resultados verificables. **P4 avanzado no cumple la aceptación semántica ni el objetivo FPS.** Este cierre no autoriza P5/P6 ni declara SUCCESS.

## Resultado verificable

- P2: archivo durable `0005_data_history`, caché/TTL/cuotas/lease, refresco autorizado, fechas UTC y revisiones. Histórico diario agregado CoinPaprika autorizado para IA personal local, separado del spot; corrección Eurostat, bloqueo Coinbase por derechos. Catálogo actual: 31 proveedores, 36 modalidades, 34 adaptadores. La pasada del 20-10 verificó 17 modalidades (16 HTTP nuevos + una caché real), 12 utilizables entonces; A21 se comprobó después con 90 observaciones. **No son 34 conexiones activas, ni una comprobación de todas hoy.** Fechas/resultados en el registro de proveedores y evidencia de datos.
- HUD: rails negros, tipografía sans serif de 16 px, históricos reales comparables, nueve clics NPC en QA anterior. Repetición final de cuatro departamentos (Research/Quant/Comité/Sistemas), sin errores JS ni overflow, pausa del avatar correcta; dossier rechazado visible. El videowall informa NO_LOCAL_MODEL y 19 fallos/bloqueos históricos, sin esconderlos.
- Research: treinta roles, jobs persistentes y resultados Python. Citas allowlisted y texto cualitativo separado de cifras exactas, sin debilitar validadores. Tres especialistas sin datos de su mandato se abstienen; no se infiere liquidez ejecutable desde históricos.
- MASTER: 10.000 EUR ficticios, cero posiciones, ledger hash `fdf208a2870b7027d00bf2c9e7f8ee78cd27c044bbca5f8bab8fcc3dcd465836`. PAPER_ONLY, orders_enabled=false, POST /api/orders=403 antes/después del restart. Cero órdenes/brokers/fondos reales, coste de servicios 0 EUR.

## Pruebas

`check-close.txt`: **212 pytest, 54 Vitest, 1 opt-in omitido**, TypeScript/build; exit0, 97,24 s. Incluye permisos, concurrencia, persistencia, grounding/inyección y regresión financiera. `audit-close.txt`: cero vulnerabilidades conocidas Python/npm, exit0. El aviso certifi se corrigió previamente, sin desactivar TLS.

`restart.json`: nueve jobs del último run mantienen IDs/estados/intentos/errores y MASTER conserva hash tras reiniciar backend. Cola0, activos0. Alembic actual0005, sin nuevas operaciones detectadas. `git diff --check` correcto. Avisos no bloqueantes conocidos: Starlette/httpx y bundle3D ~997 kB sin comprimir.

`research-p411-incomplete.json`: caso `de7188a7-de42-4318-b5ae-e77b5c86dc76`, run `history-qualitative-p411-run`. Seis jobs Python terminados; Bull FAILED/TIMEOUT tras dos intentos, Bear y Chair BLOCKED/DEPENDENCY_INCOMPLETE. **No existe debate E2E aceptado en este cierre.** El run anterior p4.10 rechazó cifras sin respaldo; p4.8 había fallado semánticamente. No se elimina ningún resultado fallido.

La abstención real con referencias insuficientes conserva el caso `65885284-5037-4346-b1fa-06808398f0cd`; el caso informativo BCE `66dc5f17-849a-4e32-a90a-76e45a7ba447` no fuerza debate. No sustituyen la aceptación generativa pendiente.

## Diagnóstico de lentitud

Dos peticiones **TEST_ONLY**, una por candidato existente, máximo128 tokens/120s, mismo texto sintético. Ningún caso nuevo ni escritura financiera. llama.cpp b11696, CPU3threads/una ranura/contexto4096. Pesos ya instalados y hash validado; Apache-2.0 para ambos Qwen; no descargas.

| Medida | Qwen3-1.7B Q8_0 | Qwen2.5-1.5B Q4_K_M |
|---|---:|---:|
| Tokens entrada / salida | 590 / 42 | 586 / 28 |
| Contexto realmente procesado / tiempo | 587 / 32,50 s | 586 / 6,03 s |
| Procesamiento contexto | 18,06 tok/s | 97,12 tok/s |
| TTFT por streaming | 33,98 s | 6,20 s |
| Generación (timing del servidor) | 6,27 tok/s | 18,73 tok/s |
| Petición total | 40,51 s | 7,49 s |
| RSS máximo proceso | 1,79 GiB | 1,75 GiB |
| Memoria privada máxima | 1,33 GiB | 0,89 GiB |
| RAM libre mínima sistema | 68,55 MiB | 2,15 GiB |
| CPU proceso media / total12 lógicos | 19,34 % | 20,51 % |
| CPU sistema media | 46,60 % | 42,70 % |
| Lecturas page-in/s sistema, media | 1.226 | 131 |
| Alimentación registrada | Batería | Red |

**Comparación observacional, no A/B causal controlado**: entre pruebas cambiaron alimentación y carga del sistema (commit~29,1→23,4GiB). No atribuir toda la mejora al modelo ni toda la paginación al LLM. Los fallos del proceso incluyen blandos; PDH Page Reads/Input son globales. No se cerraron aplicaciones del usuario ni se cambiaron ajustes de Windows. No se midió temperatura ni ancho de banda de memoria; no afirmar throttling térmico demostrado.

Carga del runtime Qwen3 previo: log `model loaded` a4,37s del arranque; no incluye verificación del hash ni garantiza páginas residentes. Qwen2.5:7,46s desde lanzar/verificarhash hasta health200; log modelo cargado a4,28s. Son medidas distintas. La paginación perezosa explica que un servidor que declara cargado aún tenga que recuperar páginas durante la primera petición; aquí el working set Qwen3 partió de~14MiB y subió a~1,79GiB.

En el run largo p4.11, los logs muestran procesamiento de contexto~11–12tok/s, generación media~3,3–4tok/s y tramos inferiores a2tok/s; además había presupuesto de razonamiento256 y hasta1400 tokens de salida. El segundo intento llegó a693 tokens generados al cancelarse. **Los timeouts no proporcionan un TTFT ni un resultado final válidos**. Un contexto de~1200 tokens y centenares de salida puede exceder300s en esas condiciones. CPU~25% máximo es compatible con tres threads sobre doce lógicos; aumentar concurrencia no es una solución demostrada.

Las mejoras ya aplicadas compactan fuentes/metadatos, seleccionan evidencia relevante, calculan features en Python, abstienen mandatos sin inputs y evitan números generados. La prueba corta desactiva thinking y compara pesos más ligeros. Su JSON válido **no demuestra grounding financiero**; Qwen2.5 mantiene fallos semánticos previos y no se promueve como modelo aceptado.

Reproducción explícita, sin otro modelo simultáneo: `python scripts/start_local_llm.py --candidate qwen25`; tomar PID de `output/p4-runtime/server.pid`; `python scripts/diagnose_p4_runtime.py --pid <PID> --output output/diagnostic.json`. Solo sin jobs activos/cola; una petición y sin retry. No ejecutar automáticamente al abrir HQ. Al cerrar este diagnóstico se descargó de RAM el proceso propio: backend/3D siguen activos y muestran NO_LOCAL_MODEL. No se ha cambiado el modelo predeterminado por uno no aceptado.

## Oficina y evidencias visuales

Medición real21-10 con cargador confirmado, avatar en movimiento y Qwen3 activo, Equilibrado1920×1080/DPR0,70–0,72: Recepción31,68; Trading33,73; Comité34,19; Sistemas37,71FPS. Cuatro ventanas válidas. **No alcanza40–45FPS.** Medición anterior en batería30,45–35,99FPS; condiciones no equivalentes. No existe una medición de FPS simultánea con Qwen2.5 que permita afirmar mejora gráfica.

Metadatos públicos: [fps-ac-llm.json](../datos-20261021/fps-ac-llm.json). Capturas auténticas actuales en `output/playwright/p4/history-{watchlist,research,quant,committee,systems,videowall}.png`; hashes en `screenshots-manifest.json`. Permanecen locales por derechos de visualización personal de CoinPaprika; no se publican valores/licencias restringidas en GitHub.

## Pendientes y recomendación

1. Falta un dossier Bull/Bear/Chair semánticamente aceptado con evidencia suficiente; la abstención y los cálculos no sustituyen ese criterio.
2. Falta cumplir40–45FPS bajo carga simultánea. La memoria disponible varía mucho; el diagnóstico identifica presión real, no una causa única.
3. P2 aún no certifica calendarios exhaustivos, universos históricos/corporate actions ni publicaciones point-in-time para un laboratorio multiactivo. Fuentes sin clave/derechos/configuración siguen explícitamente limitadas.
4. Estudiada profundidad adaptativa en [P4_PROFUNDIDAD_Y_CIERRE](../../../P4_PROFUNDIDAD_Y_CIERRE.md): vía ordinaria Python y síntesis corta opcional; profundo con Bull/Bear/Chair solo cuando sea pertinente y suficiente. La nueva modalidad compacta no está implementada ni se presenta como terminada.
5. Plan futuro [Plan_JAIME_P5_P6](../../../Plan_JAIME_P5_P6.md) registrado, con separación datos/hipótesis/experimentos/ejecución. No se inicia su implementación ni verificación comercial de brokers.

**Entrega PARTIAL. P4 no listo.** Se detienen las inferencias y el trabajo de fase tras este cierre, esperando instrucciones del usuario. No se promete otro resultado con el mismo experimento ni se requiere comprar servicios/modelos.

Logs publicados normalizados únicamente en blancos finales para `git diff --check`; el bruto permanece en `output/p4-data-refresh/`. No se cambia ningún resultado.
