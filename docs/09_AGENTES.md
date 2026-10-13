# Diez NPC, diez responsabilidades reales

| NPC | Función | Entregable |
|---|---|---|
| Elena Ruiz | Fundamental | dossier y escenarios |
| Marco Vidal | Técnico | señales y niveles con datos |
| Sofía Álvarez | Macro | régimen, tipos, curvas y FX |
| Daniel Kim | Noticias/sentimiento | fuentes fechadas y resumen |
| Lucía Ortega | Quant | backtest reproducible |
| Hugo Martín | Riesgos | veto y explicación |
| Clara Ibáñez | Ejecución | órdenes/fills PAPER y conciliación |
| Álvaro Soto | Comité | acta, decisión y condiciones |
| Irene Campos | Crítica | tesis contraria y escenarios adversos |
| Noah Vega | Auditoría/sistemas | trazas, alertas y calidad de datos |

Estados: IDLE, QUEUED, WORKING, WAITING_DATA, BLOCKED, ERROR, OFFLINE, derivados de jobs con id, started_at, heartbeat, updated_at, output_refs y error. NPC no debe parecer trabajando cuando no hay tarea real. Puede haber animaciones de reposo neutrales.

Flujo: screening → research → crítica → comité → riesgo determinista → orden paper → auditoría → postmortem. Ollama u otro modelo local opcional; sin LLM usar cálculos, reglas y reportes deterministas. Ningún agente recibe claves ni permiso de saltarse veto.
