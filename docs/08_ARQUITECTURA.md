# Arquitectura local-first, reproducible y modular

Frontend: React, TypeScript, Vite, Three.js/React Three Fiber/Drei, Tailwind, Zustand para cámara/HUD, TanStack Query para datos, librería open source de gráficos. Overlays DOM para textos financieros; el mundo 3D maneja interacción y posición, no contabilidad.

Backend: Python FastAPI, Pydantic, SQLAlchemy, Alembic y SQLite WAL; workers locales durables mediante tabla de jobs/scheduler; SSE o WebSocket para estado de agentes. Docker Compose opcional, no obligatorio. Bind a 127.0.0.1 y CORS restringido por defecto.

Capas: providers/adapters → observations → instrument registry → research → agents/jobs → quant → committee → deterministic risk → paper orders/fills → ledger → portfolio/performance → audit.

API objetivo: /health, /api/providers/status, /api/instruments, /api/quotes, /api/portfolio/positions, /api/portfolio/nav, /api/orders, /api/fills, /api/trades, /api/research/cases, /api/agents, /api/jobs, /api/risk, /api/audit, /api/events.

Todos los endpoints deben tener esquemas Pydantic, mocks, errores tipados y pruebas. Dependencias fijadas mediante lockfiles. No se requiere nube ni base de datos comercial.
