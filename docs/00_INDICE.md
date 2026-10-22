# Índice — lectura selectiva por fase

**DOCUMENTO RECTOR VISUAL (2026-10-15):** [especificación consolidada](ESPECIFICACION_DEFINITIVA_2026_10_15.md) · [plan maestro Sims/videowall/agentes](PLAN_MAESTRO_SIMS_VIDEOWALL_AGENTES_INTEGRACIONES.md).

**AUTORIZACIÓN VIGENTE (2026-10-16):** P3 está cerrada y aprobada. [P4 autorizado](AUTORIZACION_P4_2026_10_16.md) · [plan maestro P4](PLAN_P4_AGENTES_RESEARCH_LOCAL_AI.md) · [investigación IA local/grounding](INVESTIGACION_P4_ORQUESTACION_IA_LOCAL.md). **STOP ahora antes de P5**.

| Fase | Leer primero |
|---|---|
| P0 | 01_VISION, 08_ARQUITECTURA, 13_SEGURIDAD, 14_COSTE_CERO, 17_AUDITORIA_PREVIA, 18_MODELOS_Y_TOKENS |
| P1 | 02_MUNDO_3D, 03_DEPARTAMENTOS, assets/REFERENCIAS |
| P2 | 04_INSTRUMENTOS, 06_DATOS_APIS, 11_CONTRATOS, 15_FUENTES |
| P3 | 07_CARTERA_LEDGER, 12_ESQUEMA_DATOS, 20_UI_Y_FLUJOS, evidencias/P3 |
| P4 | **AUTORIZACION_P4_2026_10_16, PLAN_P4_AGENTES_RESEARCH_LOCAL_AI, INVESTIGACION_P4_ORQUESTACION_IA_LOCAL**, 09_AGENTES, 10_CUANTITATIVO, 06_DATOS_APIS, INTEGRACIONES_TERCEROS_VERIFICACION |
| P5 | 07_CARTERA_LEDGER, 10_CUANTITATIVO, 11_CONTRATOS |
| P6 | 06_DATOS_APIS, 07_CARTERA_LEDGER, 11_CONTRATOS, 13_SEGURIDAD |
| P7 | 16_TESTS_ACEPTACION, 17_AUDITORIA_PREVIA, 18_MODELOS_Y_TOKENS |

Siempre leer primero `AGENTS.md`, `STATUS.md` y `tasks/Px_*.md` correspondiente. **No cargar todos los documentos a la vez.**

## Referencias activas
- 30 roles y contratos: [09_AGENTES](09_AGENTES.md).
- Quant y sesgos: [10_CUANTITATIVO](10_CUANTITATIVO.md).
- Terceros auditados: [INTEGRACIONES_TERCEROS_VERIFICACION](INTEGRACIONES_TERCEROS_VERIFICACION.md).
- Modelos de Codex/uso de tokens: [18_MODELOS_Y_TOKENS](18_MODELOS_Y_TOKENS.md).
- Evidencia cierre P3: [evidencias/P3](evidencias/P3/README.md).

Los documentos P0-P3 históricos se conservan para auditoría, pero no reabren fases ya cerradas. P4 no autoriza riesgo formal P5 ni ejecución P6.

## P4 · estabilización posterior a QA (2026-10-19)
- [Auditoría de fallos semánticos, watchlist e integraciones](AUDITORIA_P4_CALIDAD_HUD_INTEGRACIONES_2026_10_19.md).
- [Prompt maestro Codex para corrección por gates](PROMPT_CODEX_P4_ESTABILIZACION_HUD_INTEGRACIONES_2026_10_19.md).
- [Issue #6 — seguimiento](https://github.com/jaimealonsovargas-rgb/JAIME-INVESTOR-HQ/issues/6).
- **P4 sigue pendiente de aceptación semántica**; P5/P6 no autorizados. No confundir tests correctos con análisis financiero aceptado.

## Requisitos de diseño futuro registrados (2026-10-22)
- [Realineación hacia research autónomo local](ARQUITECTURA_AUTONOMIA_P4_P5.md): contrato propuesto de eventos/tareas, dependencias y gates; P5/P6 siguen sin autorización.
- [Plan_JAIME_P5_P6](Plan_JAIME_P5_P6.md): documento aportado por el usuario, no autorización de implementación ni verificación de proveedores.
- [Profundidad adaptativa y límites de cierre P4](P4_PROFUNDIDAD_Y_CIERRE.md): encaje con los contratos existentes y condiciones para una ejecución más eficiente. **No inicia P5/P6.**
