# Actualización SEC, skills P4 y catálogo Nivel 2

04-11-2026. Alcance B2/P4; sin implementación de P5/P6. PAPER ONLY, 0 EUR, MASTER separado y órdenes HTTP 403.

## Procedencia de las instrucciones nuevas

La entrada 2026-11-03 y D027/D028 estaban en la [PR #8](https://github.com/jaimealonsovargas-rgb/JAIME-INVESTOR-HQ/pull/8), abierta y no fusionada, commit `41ccf4e41bb0927f4d718e78e1fc01d639b6f53e`. Main remoto todavía conservaba el estado de octubre. Se copiaron exclusivamente 143 archivos nuevos de `.agents/skills/`, 39 SKILL.md y licencias incluidas, sin ejecutar scripts. README local añade el pin y las reglas de integración.

Las decisiones locales D027/D028 ya tenían otro contenido: se conservan y las nuevas se registran como **D038/D039**, con referencia a los números de la PR. AGENTS incorpora invariantes 9/10. No se hizo merge, push ni sustitución de la documentación actual por documentos antiguos. No se amplía la autorización de P5/P6.

## Actualización SEC real

Migración aditiva `0012_company_updates`: outbox de actualizaciones contables, creado en la misma transacción que acepta el snapshot/recibo SEC. Solo emisores con modelo previo y contenido diferente. Clave por CIK/hash de contenido; repetir una descarga no duplica el evento. El worker SEC existente procesa eventos pendientes antes de la siguiente consulta: no hay otro scheduler.

El constructor fija snapshot y fecha de conocimiento; guarda versión inmutable y rechaza regresiones del ejercicio/informe. La clave de build del evento permite recuperar una caída entre construcción y confirmación. Los errores de datos se registran como BLOCKED; la fuente desactivada impide procesar. Lectura local: `/api/universe/issuers/{cik}/model-updates`, máximo 20 eventos.

Piloto real: job `b24-real-apple-filing-20261104`, dos consultas SEC (submissions/companyfacts), SUCCEEDED. Apple presenta el filing **0000320193-26-000026, fechado 03-11-2026**, ejercicio **28-09-2025 a 26-09-2026**. El evento genera automáticamente **versión 3 / NEW_PERIOD**; versiones 1/2 siguen disponibles. Revisión contable PARTIAL: el cambio de ejercicio no equivale a superar todas las conciliaciones.

Copia SQLite `output/b24-before-0012.db`; 37 tablas previas idénticas tras migración, integrity_check OK y Alembic sin drift. Tras el ensayo: seis modelos previos conservan payloads; tablas portfolios/ledger_events/ledger_entries idénticas. Repetir la solicitud de importación devuelve el mismo job completado. `POST /api/orders` permanece 403.

Evidencias privadas: `output/b24-update-migration.json` y `output/b24-filing-update-real.json`. Sin descargar otra vez el universo ni sustituir originales anteriores.

## Adaptación de skills al ciclo P4

Referencias: [morning-note](../../.agents/skills/morning-note/SKILL.md), [thesis-tracker](../../.agents/skills/thesis-tracker/SKILL.md), [catalyst-calendar](../../.agents/skills/catalyst-calendar/SKILL.md).

`research_workflows.py` produce artefactos deterministas ligados al caso/run, versión, pin y hash. Usa solo claims verificados con evidencia disponible, vigente y autorizada; no invoca LLM ni scripts vendoreados. La finalización del ciclo autónomo guarda los artefactos en su resultado existente. Abrir el dossier revalida los derivados contra los derechos/frescura actuales. Se muestran en un desplegable, reutilizando la consulta del dossier.

- Nota del ciclo: hasta ocho observaciones trazables; no afirma cobertura completa de noticias nocturnas ni «sin novedades» cuando faltan fuentes. Sin ideas de trade ni precio objetivo automáticos.
- Tesis: conserva run/versiones y solo presenta hipótesis respaldadas como provisionales. Si el ciclo descriptivo no formuló tesis: NO_THESIS, sin convicción, pilares o acciones inventadas. No es todavía un gestor completo de tesis analíticas.
- Calendario: exige eventos P2 confirmados, fecha con zona y horizonte de 30 días. Sin tales datos: NO_CONFIRMED_EVENTS. Los adaptadores actuales no aportan aún un calendario corporativo completo; no se estiman fechas de earnings.

Consulta HTTP del dossier real existente: ABSTAINED / NO_THESIS / NO_CONFIRMED_EVENTS por la evidencia disponible. No se repitió la campaña Bull/Bear/Chair ni se declaró aceptación semántica. **P4 sigue PARTIAL.**

## Nivel 2: catálogo, no conexiones certificadas

Yahoo C01 y Stooq C02 añadidos como **candidatos**, `data_tier=2`, `UNOFFICIAL_SOURCE`, ámbito interno y sin redistribución. Totales: 38 modalidades, 33 proveedores candidatos y 34 adaptadores implementados (no se inflan estos últimos). Sus nombres y banderas salen en calidad P2. Presupuesto propuesto: 1 consulta/h y caché 24 h; no se afirma que sea la cuota del proveedor.

La política interna tolera esta categoría, pero no otorga licencias del proveedor. Las páginas oficiales de términos consultadas no permitieron completar verificación (Yahoo 429/999; Stooq validación de navegador). Por ello los permisos de acceso/display/almacenamiento/research permanecen false, estado NOT_IMPLEMENTED y sin URL de captación ni parser activado. No se han consultado precios, generado instrumentos europeos ni hecho pasar datos por oficiales.

Continuación concreta: verificar condiciones/endpoint, identidad del listing y divisa (incluidas unidades GBp/GBP), antigüedad, ajustes y preferencia de fuente oficial; después implementar/admitir el adaptador y su piloto real. No eludir autenticación, cuotas o bloqueos. Referencias a verificar: [Yahoo](https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html), [Stooq](https://stooq.com/t/).

## Verificación

Pruebas de evento repetido, recuperación tras build, snapshot fijado y rechazo de informe anterior; workflows con evidencia revocada/caducada, jobs fallidos, fechas sin zona y ausencia de tesis; contratos frontend y representación de ausencias. `manage.py check` final: **443 pruebas backend, 93 frontend y una omisión preexistente; TypeScript/build correctos**. Primera ronda: tres expectativas del catálogo todavía en 36; corregidas a 38 modalidades/33 proveedores, sin aumentar adaptadores implementados, y check completo repetido. Alembic check sin drift y diff-check correcto. Avisos preexistentes httpx/TestClient y chunk 3D. No se añadieron dependencias ni se certificó visualmente una nueva ronda de oficina.
