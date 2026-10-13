# Estrategia Codex: GPT-6.1 Sol y GPT-6 Astra

**Los nombres y esfuerzos deben aparecer realmente en el selector de Codex.** La selección es manual: escribir el nombre en un prompt no cambia el modelo. Los límites de uso dependen del plan y pueden cambiar.

| Trabajo | Modelo sugerido | Esfuerzo | Motivo |
|---|---|---|---|
| P0 arquitectura y auditoría inicial | GPT-6 Astra | Alto | Dependencias, riesgos y diseño global |
| P1 escena 3D, cámara y rendimiento | GPT-6.1 Sol | Alto | Interacción visual compleja |
| P1 HUD, paneles y UI | GPT-6.1 Sol | Medio | Componentes acotados |
| P2 adaptadores y cache | GPT-6.1 Sol | Medio | Contratos claros |
| P2 fallos difíciles de API | GPT-6 Astra | Alto | Diagnóstico profundo |
| P3 diseño ledger/FIFO/FX | GPT-6 Astra | Alto | Invariantes financieros |
| P3 implementar tests acordados | GPT-6.1 Sol | Medio | Trabajo concreto |
| P4 agentes y workers | GPT-6.1 Sol | Medio | Flujos definidos |
| P4 grounding y seguridad | GPT-6 Astra | Alto | Control de alucinaciones y permisos |
| P5 riesgos y comité | GPT-6 Astra | Alto | Decisiones críticas |
| P5 visualizaciones cuantitativas | GPT-6.1 Sol | Medio | Implementación acotada |
| P6 idempotencia y máquina de órdenes | GPT-6 Astra | Alto | Riesgo de duplicación |
| P6 conectores tras diseño | GPT-6.1 Sol | Medio | Código testable |
| P7 pequeños arreglos/docs | GPT-6.1 Sol | Bajo/Medio | Uso eficiente |
| P7 auditoría final | GPT-6 Astra | Alto/Extra alto | Comprobación transversal |

## Cómo gastar menos uso
1. VS Code **no reduce tokens automáticamente**; evita pegar grandes bloques porque Codex lee archivos concretos.
2. Una tarea/ticket por conversación. Al finalizar actualizar STATUS.md.
3. Leer AGENTS + índice + ticket + documentación específica, no todo el repositorio.
4. Pedir diffs y pruebas del módulo, no reescribir ficheros completos.
5. Sol Medio por defecto; escalar a Sol Alto o Astra solo cuando la complejidad lo justifique.
6. Evitar modos acelerados, créditos adicionales y muchos agentes en paralelo.
7. Comparar calidad y consumo real: un modelo más potente puede resolver un bloqueo con menos iteraciones.
