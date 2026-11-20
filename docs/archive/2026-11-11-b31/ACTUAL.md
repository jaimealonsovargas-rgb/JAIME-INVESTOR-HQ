> Ficha histórica de B3.1, completada el 11-11-2026. No es la tarea activa.

# Próxima entrega única — B3.1

11-11-2026. La auditoría documental está terminada. **Próximo trabajo de código: construir el núcleo determinista inicial del laboratorio.** No está implementado todavía. Fuente del orden: [ROADMAP](../../../tasks/ROADMAP.md); estado comprobado: [STATUS](../../../STATUS.md).

## Resultado que debe entregar

Un experimento sintético de tendencia diaria reproducible, con hipótesis/parámetros tipados, costes explícitos, resultado trazable y todos los intentos registrados. Es una prueba de ingeniería; no es minería real ni aceptación de los históricos actuales.

## Alcance cerrado

1. Revisar el contrato de la primera familia de [datos/minería](../../actual/DATOS_Y_ESTRATEGIAS.md). Proponer nombres de módulos/tablas compatibles tras inspección puntual; Python 3.14 y stack actual, sin framework nuevo por defecto.
2. Genome versionado y señales permitidas. Señal conocida en t y ejecución posterior; comisiones/slippage y unidades explícitos. Separar resultado del experimento de MASTER.
3. Motor de referencia con fixture pequeño y resultado calculable a mano. Controles efectivo/buy-and-hold. No métricas con precios inventados presentadas como resultados reales.
4. Registro persistente e idempotente del intento **antes** del resultado, incluidos fallidos/descartados; hashes de datos/código/config, estado y reason codes. Migración aditiva si procede, probada en copia antes de aplicarla.
5. Pruebas relevantes: cronología/look-ahead, cálculo exacto, costes, repetición/restart, registros fallidos y conservación de MASTER. Concluir con evidencia y actualizar STATUS/esta ficha una vez.

## Aceptación

- Mismo dataset/config produce el mismo resultado; cálculo manual y costes coinciden.
- Distingue `SYNTHETIC_TEST` y dataset real. Los actuales no admisibles siguen bloqueados; no modificar flags para hacerlos pasar.
- Intentos y errores conservados; ledger, cash, posiciones y órdenes intactos. `POST /api/orders=403`.
- Entrega permite revisar qué se probó y qué falta. No añadir un panel vacío para aparentar laboratorio operativo.

## Entradas y conservación

B1 terminado; catálogo/cuentas/modelos, schema 0013, SDK/contratos IBKR y n8n piloto ya disponibles. No reinstalar, repetir bootstrap, reconstruir los 18 modelos ni reabrir la sede. Código útil: `instrument_evidence.py`, `dataset_assessment.py`, `storage_budget.py`, `company_*`, `research_*`, `cycle_*`. [Evidencias de la auditoría](../../actual/AUDITORIA_CONTINUIDAD_2026_11_11.md).

## Después de B3.1

Seguir D1 → D2 → D3 → B3.2 del ROADMAP: comprobar datos IBKR, generalizar históricos por lotes, cerrar los tres frentes de admisión y ejecutar primera campaña real. Solo una entrega activa en cada momento; el motor no espera al cierre universal de B2. IBKR permanece dentro de la ruta de datos, SEC mantiene cuentas y Alpaca el destino PAPER.

Se mantienen P4 PARTIAL, coste cero y PAPER ONLY. La semántica Bull/Bear/Chair y la escala mundial no bloquean B3.1. [Archivo de la ficha anterior](../2026-11-11-continuidad/tasks/ACTUAL.md).
