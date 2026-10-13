# Seguridad, credenciales y prohibición live

Las claves solo en .env local ignorado por Git. No variables VITE_* con secretos; no imprimir headers privados, no subir capturas de claves. Rotar credenciales expuestas previamente. Backend localhost, CORS restringido, sin acceso público por defecto.

LIVE_TRADING_ENABLED=false en ejemplo, **pero además** el código debe impedir live trading incluso si alguien cambia la variable: host allowlist paper/demo, interfaces separadas y tests de rechazo. Sin short/margin en V1. No permitir que chats o LLM envíen órdenes directamente.

Preflight: bróker PAPER autorizado, datos frescos, cash, instrumento elegible, riesgo aprobado, límites, kill switch desactivado. SUBMITTING timeout→UNKNOWN→reconciliar; no repetir órdenes no idempotentes. Registro append-only de decisiones.

Dependencias con lockfile y licencias comprobadas; protección de secretos, rate limits, auditoría de logs, backups y control de acceso si se publica en red. El usuario debe autorizar cualquier conexión que implique credenciales.
