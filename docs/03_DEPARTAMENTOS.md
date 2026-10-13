# Nueve departamentos y sus interfaces

| Departamento | Pantalla principal | Funciones |
|---|---|---|
| Recepción | Estado general | NAV, caja, agentes, alertas, último sync y mapa |
| Trading Floor | Posiciones | Activos, qty, coste, precio, P&L EUR/% y ficha profunda |
| Ejecución | Blotter | Órdenes, fills, rechazos, UNKNOWN, conciliación PAPER |
| Performance | Rentabilidad | NAV, series, atribución, realizado/no realizado, benchmark y FX |
| Riesgos | Control | Límites, exposición, liquidez, concentración, veto y kill switch |
| Research | Casos | Dossiers, valoración, fundamentales, macro, técnico, crédito y fuentes |
| Comité | Decisiones | Tesis bull/bear, críticas, votaciones, actas y condiciones |
| Quant Lab | Estrategias | Señales, backtests, parámetros, costes y escenarios |
| Sistemas | Data Quality | APIs, permisos, cuotas, errores, jobs, auditoría y frescura |

## Ficha universal
Cabecera con resumen; después secciones expandibles: instrumento, hipótesis, fuentes, valoración, catalizadores, escenarios, contraargumentos, invalidación, sizing, riesgos, opiniones de agentes, comité, orden/fills, historial de cambios, P&L y postmortem.

## Reglas de UI
Cifras con fecha/fuente/divisa; ausencia = «Sin datos», no «0» inventado. Datos de ejemplo solo en modo DEMO claramente etiquetado y nunca mezclados con mercado real. Pantallas nítidas en React, accesibles al clicar el monitor sin hablar con NPC.
