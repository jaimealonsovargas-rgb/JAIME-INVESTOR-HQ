# Revisión externa de P0 — 13/10/2026

## Alcance y método
Revisión **estática** del commit `b2563ccd3877da385a4a899a61a8024291494b5a` mediante GitHub: `STATUS.md`, contratos Pydantic, configuración, seguridad, endpoints FastAPI, persistencia/migración SQLite, frontend, scripts, pruebas y .gitignore. **No se ha ejecutado el código ni las pruebas en el ordenador del usuario**; los resultados 47 pytest + 9 Vitest, compilación y auditorías son **evidencia declarada por Codex en STATUS.md**, no reproducida independientemente.

## Resultado
**APTO para iniciar P1 (oficina 3D), con observaciones no bloqueantes.** P0 está acotada correctamente a infraestructura local. La seguridad PAPER-ONLY tiene defensas tanto de configuración como de dominio y HTTP. No existe transporte de órdenes y las URLs live se rechazan en la configuración. Los proveedores no inventan cotizaciones, las cuentas demo están separadas por contrato, las bases se migran mediante Alembic y las claves no figuran en .env.example.

## Observaciones y riesgos residuales
1. El backend es **solo local** y no implementa autenticación para acceso en red. Mantener binding a 127.0.0.1; nunca exponerlo a internet sin diseño adicional.
2. El requisito de Python `>=3.14,<3.15` y el setup que exige 3.14.x coinciden con el equipo reportado, pero limitan portabilidad. No cambiar durante P1 sin motivo.
3. La documentación menciona capturas Playwright en `output/playwright/`, directorio ignorado por Git; por tanto **no se han inspeccionado esas capturas desde GitHub**. En P1 guardar evidencias visuales reproducibles y adjuntar screenshots o incluir versiones sanitizadas con permiso.
4. `ProviderCapability` exige fecha y licencia para activar una capacidad, pero eso no verifica automáticamente derechos de uso: validar proveedores realmente en P2.
5. La allowlist exacta de URL es correcta para P0; en P6 habrá que controlar redirects, proxies, estados UNKNOWN, idempotencia, veto determinista y kill switch antes de permitir órdenes paper.
6. No existe todavía ledger, feed de datos, agentes activos ni oficina 3D; es el alcance previsto. La portada de diagnóstico P0 debe reemplazarse en P1.
7. Las imágenes conceptuales de Runway están documentadas por ID pero **no subidas como PNG**. No inventar que Codex las puede leer. Solicitar al usuario que las exporte si se necesitan como referencia visual directa.
8. La calidad 3D y rendimiento real son desconocidos hasta probar hardware, licencias y escena P1. No garantizar 60 FPS en cualquier equipo.

## Evidencia estática revisada
- `backend/app/security.py`: `deny_order_execution()` incondicional; allowlist exacta.
- `backend/app/config.py`: `Literal[False]`, paper/demo y SQLite local.
- `backend/app/main.py`: `POST /api/orders` devuelve 403; endpoints sin feeds inventados.
- `backend/app/providers.py`: adaptadores no disponibles explícitos.
- `backend/app/contracts.py`: Decimal, timestamps con zona y capacidades separadas.
- `backend/app/database.py` y migración `0001_instruments`: SQLite WAL, FK, unicidad y migración.
- `backend/tests/` y `frontend/src/api.test.ts`: cobertura de los contratos/controles principales (existencia y contenido inspeccionados, **no ejecutados aquí**).
- `.gitignore`: ignora `.env`, `.venv/`, `data/` y `output/`.
- `.env.example`: campos vacíos, sin credenciales visibles.

## Condiciones para P1
Mantener P0 verde con `python scripts/manage.py check`; preservar protección PAPER-ONLY; no tocar APIs externas ni inventar datos; abrir directamente en oficina 3D; todos los departamentos y pantallas navegables; comprobar licencias y rendimiento en hardware real; registrar pruebas y capturas. Autorizar P1 explícitamente en Codex después de `git pull`.
