# JAIME INVESTOR HQ

**Oficina 3D jugable de un fondo de inversión virtual multiactivo.**

**Estado:** P0 implementada: base local funcional de frontend, API y SQLite. La oficina 3D todavía no está implementada.
**Capital inicial:** 10.000 EUR virtuales. **Órdenes:** exclusivamente PAPER/DEMO. **Gasto obligatorio de servicios:** 0 EUR.

## Arranque local de P0 (Windows / PowerShell)

Requisitos probados: Windows 11 x64, Python 3.14.4, Node 26.3.0 y npm 11.16.0. Se fija Python 3.14.x; otros sistemas/versiones no están certificados por P0. Node debe cumplir el requisito de Vite (22.12 o superior para este proyecto). No se necesita Docker ni cuenta de proveedor.

Desde la raíz del repositorio:

```powershell
python scripts/setup.py
python scripts/manage.py check
```

El setup instala dependencias gratuitas fijadas por `uv.lock` y `frontend/package-lock.json`, crea `.env` desde el ejemplo solo si no existe y aplica Alembic. La primera instalación requiere internet para descargar paquetes públicos; no compra ni crea servicios. No activar el virtualenv ni cambiar la política de PowerShell: los scripts invocan `.exe` y `npm.cmd` directamente.

En una terminal:

```powershell
python scripts/manage.py backend
```

En otra terminal:

```powershell
python scripts/manage.py frontend
```

Abre **http://127.0.0.1:5173**. Debe aparecer la página técnica de P0 y «BASE LOCAL DISPONIBLE». El botón «Comprobar conexión» consulta realmente el backend. No es la experiencia de producto de P1 ni un prototipo 3D.

- Salud: http://127.0.0.1:8000/health
- Contrato de API: http://127.0.0.1:8000/openapi.json (sin Swagger/CDN remoto).
- Proveedores: http://127.0.0.1:8000/api/providers/status → todos «NO DISPONIBLE».
- Registro: http://127.0.0.1:8000/api/instruments → lista vacía en una instalación nueva.
- `POST /api/orders` → **403 P0_EXECUTION_DISABLED**, sin ejecución ni llamadas a brókeres.

Detener cada servidor: `Ctrl+C` en su terminal. Los puertos están fijados a 8000 y 5173, vinculados a `127.0.0.1`; si están ocupados, detener la otra instancia, sin exponer a la red.

## Verificación y mantenimiento

```powershell
python scripts/manage.py check       # pytest, Vitest, TypeScript y build
python scripts/manage.py migrate     # Alembic upgrade head; idempotente
python scripts/manage.py audit       # pip-audit y npm audit; necesita internet
.\.venv\Scripts\python.exe scripts/license_inventory.py
```

SQLite vive en `data/jaime_hq.db`, con WAL y claves foráneas. La ruta relativa se resuelve desde la raíz del repositorio. La API exige la migración correcta antes de arrancar. Para una copia manual consistente, detén el backend y copia el directorio `data/` completo; P0 no incluye un servicio de backups. No borres una base existente para resolver errores.

La configuración live o un endpoint no permitido impiden arrancar. No hay modo de activar órdenes en P0: faltan deliberadamente transporte de ejecución, credenciales, motor de riesgo y ledger. Las claves del ejemplo están vacías y no se leen en esta fase. Nunca añadir secretos al frontend, ni a variables `VITE_*`.

Resultados, incidencias y evidencia visual: [STATUS.md](STATUS.md). Arquitectura: [docs/ARQUITECTURA_P0.md](docs/ARQUITECTURA_P0.md). Licencias: [docs/LICENCIAS_P0.md](docs/LICENCIAS_P0.md).

## El producto

La aplicación abre **directamente dentro de la oficina 3D**; nunca en un dashboard plano. Una sola planta, cámara elevada en tercera persona, avatar humano, nueve departamentos, diez NPC profesionales, pantallas físicas clicables que abren interfaces financieras React nítidas y navegación WASD/teletransporte. Calidad arquitectónica premium desde la primera fase visual aceptada.

Las funciones incluyen: universo multiactivo; análisis fundamental, técnico, macro, crédito y cuantitativo; comité; riesgos con veto; posiciones y órdenes; P&L EUR; historial de cada operación; tesis, evidencias y postmortems; integraciones paper con Alpaca/Trading 212 y datos de Twelve Data cuando sus condiciones lo permitan.

## Carpetas

- AGENTS.md — reglas permanentes de Codex, seguridad y ahorro de contexto.
- CODEX_MASTER_PROMPT.md — visión completa y criterios de construcción.
- CODEX_START_HERE.md — primer mensaje que pegar en Codex.
- docs/ — diseño, instrumentos, renta fija, proveedores, contabilidad, agentes, riesgo, modelos, pruebas y auditoría.
- tasks/ — fases P0 a P7 con condiciones de salida.
- assets/ — plano SVG, paleta y referencias a imágenes de Runway.
- .env.example — nombres de variables; nunca valores reales.
- STATUS.md — progreso y pruebas, actualizado por Codex.

## Límites

No hay ejecución real, ni garantías de feeds profesionales en tiempo real para todos los activos, ni servicios remotos 24/7 con el ordenador apagado. Las imágenes conceptuales de Runway no son archivos 3D ni la aplicación terminada. Codex puede estar sujeto a límites de uso del plan existente. No activar recursos de pago sin autorización.

**Siguiente paso: revisión del usuario de P0. P1 requiere autorización y no se ha iniciado.**
