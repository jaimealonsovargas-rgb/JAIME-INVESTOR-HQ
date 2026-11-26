# JAIME INVESTOR HQ

Plataforma local de investigación financiera y futura simulación autónoma PAPER. Objetivo: un universo amplio procesado por lotes, análisis empresarial, minería de estrategias, validación, riesgo y ejecución simulada supervisados desde la oficina 3D.

## Punto de entrada único

1. [Reglas permanentes](AGENTS.md).
2. [Estado real y evidencia](STATUS.md).
3. [Próxima entrega concreta](tasks/ACTUAL.md).
4. [Orden de trabajo y esquema del sistema](tasks/ROADMAP.md).

[AUDITORÍA del 11-11-2026](docs/actual/AUDITORIA_CONTINUIDAD_2026_11_11.md): diagnóstico del atasco y decisiones para corregirlo. Las especificaciones y entregas anteriores son referencias fechadas; no crean tareas nuevas.

## Qué existe

Catálogo: 8.023 emisores SEC, 10.430 registros SEC y 14.407 instrumentos Alpaca, más un piloto ZSE. Cuentas/documentos de 100 empresas. Modelos de Apple, Microsoft y Walmart (22 versiones). Series Alpaca de 21 sesiones Apple y 252 BRK.B; esta última admitida para la primera campaña retrospectiva. IBKR: SDK y lectura de tres contratos comprobados, con divisa observada revisada; D1 ya comprobó cinco barras diarias y cotización diferida AAPL, sin archivar precios ni acreditar cobertura universal. n8n: ciclo SEC piloto en sombra, sin circuito completo de inversión.

El laboratorio B3, la validación B4 y el riesgo B5 alimentan B6. La decisión de B5 se puede consultar en Sistemas → Casos y entregas. La [cola durable](docs/actual/ENTREGA_B6_2.md) conserva los intentos de envío. El simulador concilia cada ejecución con su orden y reconstruye efectivo y posiciones tras un reinicio. La apertura controlada de Alpaca PAPER queda pendiente. P4 sigue PARTIAL. [Conciliación B6.3](docs/actual/ENTREGA_B6_3.md) · [Simulador B6](docs/actual/ENTREGA_B6_1.md) · [Riesgo B5](docs/actual/ENTREGA_B5.md) · [Validación B4](docs/actual/ENTREGA_B4.md) · [Laboratorio B3.2](docs/actual/ENTREGA_B3_2.md).

## Proveedores y destino

- **IBKR:** forma parte de la ruta de datos. Contratos y acceso acotado a datos probados; captación por lotes condicionada a derechos de archivo/uso y coste cero. Sin transporte de órdenes IBKR en el alcance vigente.
- **SEC:** cuentas y documentos de empresas.
- **Alpaca:** lectura de mercado estadounidense existente y ejecutor PAPER previsto para B6.
- Trading 212, Yahoo/Stooq y más plazas: capacidades/referencias conservadas, fuera de la próxima entrega. [Matriz de cobertura](docs/actual/PROVEEDORES_Y_COBERTURA.md).

Presupuesto obligatorio 0 EUR; MASTER 10.000 EUR ficticios, separado de brokers/backtests; LIVE excluido y órdenes actualmente bloqueadas. Treinta roles lógicos no equivalen a treinta modelos trabajando simultáneamente.

## Operación y referencias

Comandos locales existentes: `python scripts/manage.py backend`, `python scripts/manage.py frontend`. [n8n](integrations/n8n/README.md) · [IBKR](integrations/ibkr/README.md) · [Arquitectura](docs/actual/VISION_Y_ARQUITECTURA.md) · [Índice](docs/00_INDICE.md).

No reinstalar ni repetir bootstrap para continuar. La fecha de un test anterior no acredita que se haya ejecutado de nuevo. [Archivo de planes sustituidos](docs/archive/2026-11-11-continuidad/README.md).

19-11-2026: [B3.2 completado](docs/actual/ENTREGA_B3_2.md), 111 tests, diez reproducciones exactas, MASTER intacto y schema0015 conservado. La revisión de uso personal local Alpaca no autoriza redistribución ni comercialización. El diagnóstico legacy de UI permanece aparte; archivo IBKR denegado por alcance de cuenta/uso/retención no acreditado, no prohibición universal.
