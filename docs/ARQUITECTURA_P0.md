# Arquitectura implementada en P0

## Límite de la fase

Base ejecutable local con frontend React/TypeScript/Vite, TanStack Query para consultar salud, backend FastAPI/Pydantic y SQLite/SQLAlchemy/Alembic. No se implementan el mundo 3D, datos de mercado, agentes, ledger, riesgo ni ejecución. El punto de entrada actual es una página temporal de diagnóstico identificada como P0; P1 deberá sustituirla por la oficina 3D completa según sus requisitos.

## Módulos y dependencias

```text
frontend/src/App.tsx → api.ts → GET /health (proxy local Vite)
                                  ↓
backend/app/main.py → contracts.py + database.py → SQLite WAL
                   → providers.py (sin conexión)
                   → security.py (órdenes siempre denegadas)
                   → config.py (solo SQLite y PAPER/DEMO)
backend/migrations → Alembic → instruments + alembic_version
```

El navegador no conoce claves ni SDKs de bróker. El backend no contiene clientes de red hacia proveedores. Solo las herramientas de instalación y auditoría contactan registros públicos. API en `127.0.0.1:8000`, frontend en `127.0.0.1:5173`; CORS permite únicamente ambos orígenes locales del frontend (localhost y 127.0.0.1). La lista de hosts reduce ataques de DNS rebinding; no es autenticación ni una autorización para publicar la API en internet.

## Contratos y persistencia

- `Instrument`: UUID, symbol/venue/currency, clase multiactivo, país e identificadores ISIN/CUSIP/FIGI opcionales, términos de bono opcionales y capacidades independientes por proveedor.
- `ProviderCapability`: research, valuation, internal_paper, broker_paper; todas deshabilitadas por defecto. Habilitar una exige fecha con zona horaria, licencia y motivo. No supone una comprobación automática de derechos.
- `Quote`: Decimal finito, proveedor, timestamp con zona horaria, divisa, retraso y flags; es un contrato, no un feed.
- `AccountScope`: MASTER / ALPACA_PAPER / T212_DEMO; sin balances ni tablas de ledger todavía.
- `MarketDataProvider`: protocolo para estado, catálogo y cotización. Stub explícitamente no disponible, sin precios de relleno.
- `DisabledPaperBroker`: interfaz separada, destino paper/demo validado; toda llamada a submit falla antes de cualquier transporte.
- `Health` y `ApiError`: respuesta tipada de salud y errores sin detalles internos del SQL.

Registro vacío persistente, sin endpoint público de escritura en P0. La migración crea unicidad de symbol/venue/currency; los identificadores y capacidades están en JSON validado por Pydantic. Sesiones por petición, transacciones explícitas, WAL, foreign_keys=ON y busy_timeout de 5 segundos. No usar `create_all` para el esquema de producción. Tests crean bases temporales, revierten migraciones y comprueban que no exista drift entre ORM y Alembic.

## Seguridad comprobada

Configuración congelada, live rechazado incluso mediante variables de entorno, allowlist exacta de bases paper/demo. Se rechazan esquemas HTTP, subdominios, userinfo, query, fragmentos, puertos y rutas alteradas. La capa HTTP devuelve 403 para cualquier orden, incluso paper; el guard de dominio también la deniega. No hay excepción para LLM, short, margen, riesgo aprobado o kill switch desactivado: ninguna orden es ejecutable.

Credenciales ignoradas por el código P0; `.env` y bases/logs/entornos están excluidos de Git. Errores de configuración ocultan valores de entrada, errores SQL se transforman en errores tipados y los access logs están desactivados. El navegador no recibe valores `.env`, incluidos VITE_*. Las pruebas de red permiten exclusivamente loopback para el event loop de Windows; no contactan brokers ni proveedores.

La protección cubre el código P0, no cambios futuros arbitrarios ni software ajeno en el ordenador. P6 deberá validar destino final de cada petición, bloquear redirects/proxies a live, exigir riesgo determinista, kill switch, reconciliación UNKNOWN e idempotencia. No se afirma que estos sistemas futuros estén implementados.

## Reproducción y continuidad

`scripts/setup.py` → uv sync --locked + npm ci + migración. `scripts/manage.py` → migrate/backend/frontend/check/audit. Dependencias exactas en pyproject/package.json; dependencias transitivas y hashes en uv.lock/package-lock.json. No publicar builds ni desplegar en servicios externos.

Licencias y fuentes: [LICENCIAS_P0.md](LICENCIAS_P0.md). Comandos: [README](../README.md). Pruebas y checkpoint: [STATUS](../STATUS.md).

Antes de P1: revisión del usuario, confirmar alcance visual y recursos de hardware para nueve departamentos y avatar; verificar licencias/atribuciones de cada asset al seleccionarlo. No hace falta ninguna clave de bróker para P1. Las capacidades externas se comprobarán en P2, la contabilidad en P3 y las órdenes paper en P6.
