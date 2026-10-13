# Estado del proyecto

- **2026-10-13 · P0_BASE terminada técnicamente; pendiente de revisión del usuario. P1 NO iniciada.**
- Aplicación ejecutable: **SÍ**, base técnica local de frontend, backend y SQLite. Sin oficina 3D simplificada ni assets 3D incorporados.
- Servicios contratados, créditos comprados y despliegues: **NINGUNO**. Coste adicional de servicios: **0 EUR**.
- Órdenes live y paper: **BLOQUEADAS en P0**, sin transporte de ejecución.
- Integraciones con claves reales: **NO**. Alpaca Paper, Trading 212 Demo y Twelve Data: **NO DISPONIBLE**, acceso no comprobado.
- Cotizaciones, trades, beneficios y actividad de agentes: **no generados**. Registro de instrumentos inicialmente vacío.
- Ledger de 10.000 EUR ficticios: **pendiente de P3**, separado por diseño de cuentas demo. No se ha creado un saldo provisional ni sumado cuentas.
- Secretos nuevos: **NINGUNO**. `.env` local creado desde el ejemplo, credenciales vacías, excluido de Git.
- Modelo/esfuerzo seleccionado por el usuario: no consta confirmación del selector; no se ha cambiado automáticamente ni se han lanzado subagentes.

## Implementado

| Área | Archivos y resultado |
|---|---|
| Frontend | `frontend/src/`, `index.html`, TS/Vite. React 19.3.0, TypeScript 7.0.2, Vite 8.3.4, TanStack Query 5.104.2. Página técnica P0 en español; comprobación real de salud, recuperación de errores y adaptación móvil. |
| Backend | `backend/app/{main,config,contracts,database,providers,security}.py`. FastAPI 0.143.0, Pydantic 2.14.1, SQLAlchemy 2.1.4, Uvicorn 0.54.0. Salud, proveedores, instrumentos, bloqueo de órdenes y OpenAPI local. |
| Base de datos | `alembic.ini`, `backend/migrations/`, revisión `0001_instruments`. Alembic 1.20.0, SQLite WAL, claves foráneas y busy_timeout. Registro vacío con UUID y unicidad símbolo/mercado/divisa. Arranque exige migración. |
| Contratos | Instrumentos multiactivo, capacidades independientes con fecha/licencia/motivo, términos de bono, cotización Decimal con procedencia, ámbitos MASTER/ALPACA_PAPER/T212_DEMO. Interfaces de datos y broker bloqueado sin red ni credenciales. |
| Seguridad | Configuración congelada; rechazo de live y URLs fuera de allowlist exacta; denegación incondicional de órdenes en dominio/API; hosts/CORS locales; sin access logs ni Swagger/CDN; sin exposición de `.env` al navegador. |
| Reproducción | `pyproject.toml`, `uv.lock`, `.python-version`, `frontend/package-lock.json`; `scripts/{setup,manage,license_inventory}.py`. Herramientas `.tools/`, entorno `.venv/`, DB `data/`, ignorados por Git. |
| Pruebas y documentación | `backend/tests/`, `frontend/src/api.test.ts`, `output/playwright/`; README, decisiones D010–D015, `docs/ARQUITECTURA_P0.md`, `docs/LICENCIAS_P0.md` e índice actualizados. |

## Entorno y licencias

Windows 11 Pro x64 10.0.26200; Node v26.3.0; npm 11.16.0; Python 3.14.4; SQLite 3.50.4; Git 2.55.0.windows.3; uv 0.13.0. No se modificó la política de PowerShell ni se instalaron servicios de sistema. Otros sistemas/versiones no certificados por esta fase.

Dependencias directas y transitivas inventariadas desde METADATA/LICENSE y package-lock: [LICENCIAS_P0.md](docs/LICENCIAS_P0.md), con versiones y fuentes oficiales. Sin suscripciones de software, fuentes descargadas ni assets de terceros en P0. Recursos y rendimiento 3D pendientes de P1.

## Pruebas ejecutadas: resultados reales

| Comando / comprobación | Resultado final |
|---|---|
| `python scripts/setup.py` | OK: uv sync --locked, npm ci, creación no destructiva de .env y migración local. |
| `python scripts/manage.py check` | **47 tests pytest + 9 tests Vitest aprobados; TypeScript y build Vite correctos.** Última batería completa: 13-10-2026, 18:35 Madrid. Un aviso de deprecación, descrito abajo. |
| Backend | Salud/arranque, DB ausente/degradada, migración up/down/up e idempotencia, Alembic sin drift, WAL/FK, persistencia tras reconexión, unicidad, contratos/Decimal/procedencia, CORS/hosts, live y URLs manipuladas rechazados, órdenes paper/live denegadas, secretos no expuestos. Tests permiten solo loopback para asyncio Windows; sin conexiones externas. |
| Frontend | Acepta contrato paper válido; rechaza LIVE, órdenes habilitadas, DB fallida, fecha inválida y respuestas incompletas; maneja HTTP 503 y desconexión. |
| `python scripts/manage.py audit` | **pip-audit: sin vulnerabilidades conocidas. npm audit: 0 vulnerabilidades**, según bases consultadas el 13-10-2026. No equivale a garantía absoluta. |
| HTTP real local | Health/proveedores/instrumentos/OpenAPI: 200. Instrumentos `[]`; proveedores NO DISPONIBLE y checked_at nulo. POST local `/api/orders` con modo live: **403 P0_EXECUTION_DISABLED**, sin contacto con bróker. `/docs`: 404, sin CDN. |
| Red | `Get-NetTCPConnection`: 8000 y 5173 escuchan exclusivamente en 127.0.0.1. Recursos del frontend observados únicamente desde origen local. |
| Playwright/Chromium | Escritorio 1440×1000 y móvil 390×844 revisados visualmente. Botón funcional; backend detenido → NO DISPONIBLE; reiniciado → BASE LOCAL DISPONIBLE. |
| Variables frontend | Build con marcador ficticio VITE_SECRET_SENTINEL: marcador ausente de dist. Variable retirada después; ningún secreto real usado. |
| Git/seguridad | .env, DB/WAL, entornos y node_modules excluidos; credenciales locales vacías. Revisión manual: sin cliente de ejecución ni ruta de órdenes habilitable. |

Evidencia real sin credenciales: [escritorio](output/playwright/p0-desktop.png), [móvil](output/playwright/p0-mobile.png), [backend desconectado](output/playwright/p0-offline.png). No son renders de una oficina futura.

## Incidencias y limitaciones

1. PowerShell bloqueó `npm.ps1`: resuelto con `npm.cmd`, sin modificar la política del equipo.
2. Primer aislamiento de red bloqueó socketpair interno de asyncio Windows (2 fallos y 10 errores). Corregido permitiendo solo loopback; batería final aprobada.
3. Primera llamada de pip-audit llevaba `--disable-pip` sin requirements: corregida; auditoría final OK.
4. Una llamada a Vitest coincidió con la reinstalación npm ci y no encontró el binario. Se terminó setup y se repitió check secuencialmente: 9/9 y build correctos. Ejecutar setup y check en secuencia.
5. Favicon inicialmente ausente: corregido con SVG propio embebido. La caída intencionada del backend produjo el error HTTP esperado y NO DISPONIBLE.
6. **Mantenimiento no bloqueante:** Starlette 1.8.0 avisa que TestClient con httpx está deprecado a favor de httpx2. Los 47 tests pasan con el lock actual; evaluar la migración del cliente al actualizar dependencias. El aviso no se oculta.
7. uv informa que ignora el entorno `.tools` del bootstrap y utiliza `.venv`, comportamiento previsto. Sin cambios globales.
8. No hay autenticación de red, backups automáticos, feeds, jobs, ledger, motor de riesgo ni ejecución. La aplicación es exclusivamente local. Guardas de redirects, preflight, kill switch y reconciliación UNKNOWN deberán implementarse antes de permitir órdenes paper en P6.

## Comandos de comprobación

Desde la raíz, en PowerShell:

```powershell
python scripts/setup.py
python scripts/manage.py check
```

Después, en dos terminales distintas:

```powershell
# Terminal 1
python scripts/manage.py backend
```

```powershell
# Terminal 2
python scripts/manage.py frontend
```

Abrir **http://127.0.0.1:5173**, pulsar «Comprobar conexión» y comprobar «BASE LOCAL DISPONIBLE». Salud: **http://127.0.0.1:8000/health**. Parar con Ctrl+C. No hacen falta claves. Más detalles en [README](README.md).

Se dejaron los servidores de comprobación ejecutándose en localhost para facilitar la revisión; no son servicios permanentes ni se garantiza que sobrevivan al cierre de la sesión. Si un puerto está ocupado, comprobar la instancia existente antes de arrancar otra.

## Siguiente paso

**Sin bloqueos técnicos de aceptación de P0. Falta revisión y autorización del usuario para P1.** Al iniciarla, comprobar hardware/rendimiento y seleccionar recursos gratuitos con licencias y atribuciones verificadas. No se ha adelantado trabajo artístico. La entrada final deberá ser el mundo 3D con nueve departamentos reales conectados.

Datos externos corresponden a P2, ledger de 10.000 EUR a P3, agentes a P4, riesgo a P5, ejecución paper a P6 y auditoría global a P7. Ninguna de esas funciones se declara implementada aquí. **Detenido tras P0.**
