# P4: subconjunto controlado de integraciones

Revisión local 2026-10-18. Vibe-Trading permanece fijado a `d7f1b9e22b42c10197497a8e2cac4f0e2cc9ca1e` (v0.1.16, MIT y NOTICE ya conservados). No se instaló ni importó su runtime. Se inspeccionaron el contrato de operadores `agent/src/factors/base.py`, `zoo/academic/carhart_mom.py` y `agent/backtest/optimizers/equal_volatility.py` del pin, sin ejecutarlos.

El momentum académico requiere una ventana de 252 sesiones y universo transversal: **no es aplicable a las diez referencias diarias disponibles del BCE**. La optimización de pesos pertenece a una fase posterior. No se habilitan esos presets ni se presentan los cálculos HQ como una reproducción de Carhart o un backtest Vibe.

P4 utiliza ocho descriptores propios, pequeños y auditables en `backend/app/research_evidence.py`, con Decimal, input hashes y evidence IDs:

| Descriptor | Definición sobre observaciones comparables |
|---|---|
| period_return | último / primero − 1 |
| mean_level | media aritmética de niveles |
| sample_volatility | desviación muestral de cambios relativos, sin anualizar |
| last_change | último / penúltimo − 1 |
| range | máximo − mínimo |
| min_level | mínimo observado |
| max_level | máximo observado |
| z_score | (último − media) / desviación muestral de niveles |

Se exige muestra de al menos tres observaciones positivas, misma fuente/feed/serie/unidad/venue; no se mezclan unidades ni se fabrican OHLC. Series constantes dejan z-score no disponible. Son estadísticas descriptivas, no señales ejecutables, alpha, rendimientos de cartera o validación de estrategias. Las noticias no se convierten en precios. La selección de presets de estrategia Vibe queda bloqueada por insuficiencia de datos y alcance P5; no se afirma tener equipos Vibe operativos.

Agent Reach sigue limitado al RSS oficial BCE A20, canal ya auditado en el pin `94f06c1969dfc1834001269d79d3ad0972d9dee6`. Se reutiliza el cliente seguro HQ P2, no cookies ni cuentas. Solo metadatos sanitizados y atribuidos, marcados UNTRUSTED_CONTENT. No hay canales nuevos aprobados por inferencia.

Liquid OAuth continúa bloqueado por scope read+trade. Ningún agente recibe shell, herramientas de bróker, ejecución de código generado, secretos o facultad de escribir fuera de research.
