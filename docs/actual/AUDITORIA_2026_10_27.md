# Auditoría crítica de JAIME — 27-10-2026

Informe de partida conservado como evidencia histórica. Después de esta auditoría se implementó [B1](ENTREGA_B1.md) y el usuario autorizó P6 Alpaca PAPER; el estado vigente está en [STATUS](../../STATUS.md).

Base inspeccionada: `5b56dc8e699a73e6d4b9519a03088e5b05151b8e`; Git limpio al iniciar. Lectura del chat **Construye la base P0 de JAIME**, documentación, código y capturas históricas; tres reproducciones sintéticas en SQLite en memoria. Sin arrancar la app, consumir LLM, modificar base personal, ejecutar órdenes o captar precios nuevos. La entrega final modifica organización/documentación y añade evidencia de auditoría, no corrige todavía estos bugs.

## Dictamen

La visión profesional ya estaba escrita, especialmente en Plan_JAIME_P5_P6. El desarrollo ha producido oficina, infraestructura, guardas y una revisión descriptiva pequeña, pero no un proceso completo de inversión. Contar proveedores/roles/tests ha ocultado que faltan cobertura empresarial, modelos financieros, experimentos y selección. P4 sigue PARTIAL; P5 está autorizada pero sin implementar.

La base útil merece conservarse: ledger separado, restricciones de órdenes, provenance, abstención, persistencia, idempotencia, API local, oficina e historial. La solución es reparar contratos y entregar flujos verticales comprobables, no aumentar capas de agentes o rehacerlo todo.

## Fallos abiertos prioritarios

Referencias de línea válidas para la base anterior a esta reorganización. Severidad se refiere al uso previsto, no a un incidente financiero real.

| ID | Hallazgo y evidencia | Impacto / siguiente acción |
|---|---|---|
| D01 Alta | `backend/app/data_parsers.py:67,185` identifica por fuente/serie/periodo/hash global; `data_history.py:14` archiva por ese ID. Fixture SEC: 2 revisiones, 1 ID, 1 fila retenida | Pérdida de versiones. Identidad semántica + revisión/filing y disponibilidad temporal; prueba as-of |
| D02 Alta | `data_parsers.py:67`, `data_history.py:35`, `research_evidence.py:35`: cambio en respuesta genera nuevos IDs y límite se aplica antes de deduplicación semántica. Dos descargas de 60 días, un precio corregido: 60 filas devueltas, solo 30 fechas únicas | Inflación de histórico y muestra útil recortada. Dedupe/revisión antes de ventana, sin perder provenance |
| D03 Alta | `data_registry.py:30` hace continue si el instrumento existe, antes de alias en :35. Fixture dos proveedores conserva alias de uno | Enriquecimiento/fallback multiproveedor incompleto; persistir alias independientemente de alta del instrumento |
| D04 Alta | `research_planning.py:27` exige filing/financial_statement; P2 entrega fundamental_fact (`data_contracts.py`, catálogo A09) | Roles fundamentales/valoración no tienen puente de datos compatible. Normalizar y verificar suficiencia, no quitar la guarda |
| D05 Alcance | `data_catalog.py:53,108` fija SEC Apple y A21 BTC; `data_parsers.py:187` solo cuatro tags SEC; `research_router.py:15` solo A21 descriptivo | Catálogo de adapters no equivale a miles de empresas. Entity/Listing, fuentes parametrizadas, lotes y cobertura |
| U01 Alta | `frontend/src/world/MonitorOverlay.tsx:31,38` fija live y deriva Disponible de health | Estado engañoso para funciones no implementadas. Contrato de capacidades separado |
| U02 Alta | `frontend/src/world/Personnel.tsx:8` entrega departamento, no persona | No existe ficha individual. Propagar persona/roles y mostrar trabajo real |
| U03 Alta | `frontend/src/world/FinancialHud.tsx:29` conserva fechas dentro del detalle | Fecha no visible en rail cerrado; DataStamp junto a precio |
| U04 Media | `MonitorOverlay.tsx:40` monta ResearchPanel en todos los departamentos; ResearchPanel mezcla formulario, runtime, cola y dossier | Sustituir panel genérico por vistas de dominio y resultado primero |
| U05 Media | `HQVideowall.tsx:47` etiqueta por existencia de value como LEDGER MASTER | Agentes puede llevar etiqueta contable incorrecta; etiqueta por dominio |
| U06 Alcance | Estado local/selects en ResearchPanel/App/World; sin centro de activos paginado ni rutas por objeto | No escala para universo amplio; búsqueda y ficha enlazable |
| Q01 Alcance | No hay StrategyGenome/StrategyStore/backtester/gates readiness implementados | Minería y selección son especificaciones; B3/B4 deben entregar motor y validación |

Las ubicaciones de frontend se precisan según el árbol real en la validación documental; los nombres de componente son la referencia de búsqueda si cambia su carpeta.

## Errores de dirección y organización

- README aún describía P1.A–B; CODEX_START_HERE ordenaba ejecutar P0. El prompt maestro mezclaba WASD/cámara detrás/diez personas con la oficina isométrica/flechas/16 NPC.
- AGENTS, índice y tasks conservaban STOP P5 aunque el usuario ya respondió «Autorizo P5, pero antes haz lo que te he pedido. Se mas critico y mejora el producto» en el chat anterior. En la fecha de esta auditoría, P6 aún no estaba autorizada; la autorización posterior consta en STATUS.
- STATUS acumulaba una bitácora extensa como entrada principal. Varios planes se autodefinían rectores y mezclaban diseño, resultados pasados y estado vigente.
- Se dedicaron sucesivos cierres a formato/latencia Bull/Bear/Chair sin datos suficientes para buena investigación fundamental. Esos fallos deben conservarse, pero no dirigir la siguiente fase.
- La interfaz organiza el trabajo por infraestructura/fases, no por empresa, modelo, tesis, tarea y experimento. El diseño visual debe reflejar esos objetos.
- No hay demostración integral empresa → dato fiable → análisis útil → hipótesis → experimento → descarte/selección. Ese es el criterio de producto que faltaba.

## Evidencia y límites

Sondas sintéticas: [resultados](evidencias/probes.json) y [script de reproducción](evidencias/probe_data_integrity.py). Usan fixtures, no precios reales, y base en memoria. Sirven para demostrar fallos; no son correcciones ni backtests financieros.

La subauditoría leyó metadatos del archivo principal SQLite con `immutable=1`, excluyendo WAL: 99 instrumentos (96 macro, 2 cripto y 1 FX), sin acciones en esa lectura. **No es inventario vivo ni prueba de ausencia absoluta de acciones**, y no se utiliza como cobertura certificada. El hallazgo sólido de alcance está en los presets y rutas de código.

La última regresión completa registrada por el proyecto fue 26-10: 317 backend y 63 frontend, más TypeScript/build. Son resultados históricos, no repetidos en esta reorganización. La subauditoría informó 14 tests puros correctos y una ejecución más amplia interrumpida sin concluir; no se atribuye un PASS integral. El detector mecánico de UI no halló patrones, lo que no refuta los problemas semánticos. No hay nueva medición de FPS, accesibilidad o apariencia live.

## Decisiones

Una entrada corta (README/AGENTS/STATUS/ACTUAL), un roadmap B0–B6 y documentación vigente en docs/actual. Retirar prompts antiguos de la ruta activa, conservar evidencia/licencias/plan original y mover bitácora al archivo. No borrar assets, modelos, entornos, bases o scripts por parecer antiguos. No se ha identificado un archivo personal inequívocamente ajeno que justifique destruirlo.

Primero B1: integridad y paneles honestos. B2: universo y modelos empresariales. B3/B4: minería y validación. B5: autonomía ampliada y riesgo. B6: PAPER futuro. [Roadmap](../../tasks/ROADMAP.md) · [tarea siguiente](../../tasks/ACTUAL.md).

## Cierre de la reorganización

Paquete aplicado y comparado por SHA-256: 52 archivos escritos, ocho originales retirados de la ubicación anterior tras conservarlos en archivo y copia local. Validación de 364 enlaces Markdown locales: cero destinos ausentes. `git diff --check` correcto. Reejecutado `.venv/Scripts/python.exe -B docs/actual/evidencias/probe_data_integrity.py`: reproduce SEC 2→1 revisiones, alias 2→1 proveedor e histórico 60 filas/30 fechas; código de salida 0 de la sonda, no PASS de corrección.

Informe HTML entregado en la carpeta outputs del chat: estructura/enlaces internos/tabs verificados estáticamente y JavaScript con `node --check`. No revisión visual: política del navegador impidió abrir URL file; no se intentó eludirla. Resultado técnico guardado en `evidencias/validacion_reorganizacion.json`. Cambios locales sin commit/push; ninguna modificación del código de aplicación ni de sus dependencias.
