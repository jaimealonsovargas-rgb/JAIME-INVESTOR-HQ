# Auditoría breve de continuidad — 11-11-2026

**Conclusión:** existe una base útil de producto, datos, contabilidad y coordinación. Todavía no existe el motor de minería. El atasco combina ampliación prolongada del piloto, instrucciones antiguas visibles y falta de una entrega próxima que produzca código de laboratorio. Esta auditoría ordena el trabajo; no implementa B3 ni aprueba históricos.

## Dónde estamos realmente

Contraste de código, base SQLite en lectura y entregas conservadas. Recuento local a las **17:02 Europe/Madrid**; las comprobaciones de conectividad/test anteriores mantienen su fecha y no se presentan como ejecutadas hoy de nuevo.

| Pieza | Estado comprobado | Diferencia respecto al objetivo |
|---|---|---|
| Oficina y paneles | Sede aceptada; activos, cuentas/modelos, calidad y ciclos visibles | Falta el producto de laboratorio junto a su motor |
| Universo | 10.430 registros SEC y 14.407 Alpaca, más HT/ZSE; 8.023 emisores SEC según directorio | Un nombre catalogado no implica datos suficientes ni elegibilidad |
| Empresas | `companyfacts` y `submissions` de 100 emisores; 18 modelos, Apple v7/Microsoft v5/Walmart v6 | La revisión/modelización amplia no está hecha; Walmart mantiene un ratio pendiente |
| Mercado | Una serie Alpaca con 21 barras Apple | Faltan profundidad, procesamiento por lotes y aceptación histórica |
| IBKR | SDK, Paper/read-only y contratos AAPL/MSFT/WMT probados; divisa observada revisada | Precios/históricos, acceso concreto y adaptador continuo pendientes |
| n8n / research | Ciclo SEC piloto implementado/probado; cinco ciclos persistidos PARTIAL; roles y flujos parciales | Último motivo ACCOUNTING_REVIEW_COMPLETE con revisión parcial; no existe circuito autónomo completo de inversión; P4 PARTIAL |
| Minería / validación | Especificaciones existentes; no se localizaron implementaciones de StrategyGenome, BacktestEngine ni ExperimentRegistry en `backend/app` | B3/B4 están por construir |
| Riesgo / PAPER | Guard incondicional de órdenes existente | Sin RiskEngine/OMS completos; B5/B6 posteriores |

La base conserva `0013_shadow_cycles`. La auditoría no lee valores de `.env`, no conecta a brokers, no descarga precios y no ejecuta scripts vendoreados.

## Qué estaba provocando desvíos

1. **Arranque desactualizado.** `CODEX_START_HERE.md` aún apuntaba a schema 0011, conciliación B2.4 y n8n futuro, aunque esos trabajos ya estaban entregados.
2. **Órdenes históricas contradictorias.** Los tickets P4/P5 mostraban P5/P6 «no autorizados», STOP, «NO IBKR» y nuevas confirmaciones. El mandato posterior ya autoriza desarrollar P5/P6 PAPER y usar IBKR en datos. La contradicción podía reaparecer al buscar texto.
3. **Demasiadas colas aparentes.** STATUS (27 KB), ACTUAL (12 KB), evaluaciones y entregas mezclaban hechos pasados con varios «siguientes pasos». Algunos documentos vigentes de proveedores seguían diciendo que no había claves ni acciones.
4. **Permiso para construir B3 desaprovechado.** ROADMAP ya permitía contratos/fixtures tras B1. Se había tratado el cierre completo de B2 como requisito de cualquier avance en minería. Solo los experimentos reales requieren datasets admisibles.
5. **Piloto confundido con alcance.** Tres empresas eran aceptación/regresión. La captación y la identidad revisada todavía no generalizan automáticamente ese trabajo a miles; el plan debe producir lotes recuperables y cobertura por activo, sin profundizar indefinidamente en las mismas tres.
6. **Readiness aún no implementada completamente.** En `dataset_assessment.py`, identidad histórica, acciones corporativas, tiempo, universo y derechos siguen bloqueados mediante condiciones fijas; el resultado BACKTEST también es fijo. No basta descargar más barras: faltan validadores que puedan justificar aceptación o rechazo por familia. No se han cambiado esas condiciones en esta auditoría.

## Qué falta y cómo se resolverá

La única secuencia está en [ROADMAP](../../tasks/ROADMAP.md), con criterios de salida. **Próxima entrega B3.1:** motor de referencia y registros con fixtures sintéticos. Después D1 comprueba datos IBKR; D2 generaliza la captación; D3 implementa admisión; B3.2 ejecuta primera campaña real solo si hay datos aceptados.

Los tres cierres de datos son identidad durante el periodo, serie suficiente/coherente y uso/cronología/universo admisibles. Para cada uno se necesita evidencia y resultado verificable; no una nueva etiqueta de aprobado. Un acceso denegado o dato insuficiente es un resultado documentado que orienta la siguiente corrección.

La cobertura objetivo sigue siendo amplia. Toda empresa no necesita treinta inferencias simultáneas: selección por eventos/capacidad, lotes, cuotas y recursos. La primera familia será tendencia diaria; valoraciones DCF, tesis LLM profundas, intradía, streaming masivo y cobertura mundial completa no son sus prerrequisitos.

**IBKR permanece dentro de la ruta de datos.** SEC conserva cuentas; Alpaca conserva lectura existente y la ejecución PAPER prevista. Comprobar acceso a un dataset IBKR no equivale a contratarlo ni a cambiar el ejecutor.

## Qué se ha retirado de la ruta activa

- P0–P7 anteriores pasan a referencias de archivo con enlaces desde sus nombres originales. Se conservan especificaciones útiles y evidencias; sus STOP y próximos pasos no gobiernan el proyecto.
- STATUS queda como fotografía corta y ACTUAL como una sola ficha. README/arranque apuntan a ellas. Arquitectura, evaluación IBKR y matriz de proveedores se alinean con esa cola.
- Se aparcan nuevos conectores/plazas, Yahoo/Stooq, cambio de ejecutor, debate profundo P4, otra reforma visual y cambios de infraestructura sin necesidad medida. No se borra su código ni investigación.
- Las previsiones de horas de la conversación son orientativas, no un calendario validado. Se mide avance por una entrega funcional aceptada; número de tests, documentos o proveedores por sí solo no mide proximidad al objetivo.

## Regla para continuar sin desviarse

Leer ACTUAL → comprobar dependencias de esa entrega → implementar → verificar → actualizar estado una vez. Una tarea nueva debe resolver un criterio de aceptación de la entrega activa; si no lo hace, se aparca en ROADMAP. Un bloqueo repetido requiere hipótesis de corrección o alternativa explícita, no repetir auditorías idénticas. Cambiar el orden solo por evidencia o instrucción del usuario, dejando motivo.

## Conservación y verificación de esta auditoría

22 documentos anteriores preservados con inventario de SHA-256, encabezado inactivo y enlaces relativos reubicados en [archivo](../archive/2026-11-11-continuidad/README.md). No se han eliminado código, datos, modelos, entornos, SDK, workflows ni evidencias. Las modificaciones son documentales.

Evidencia privada de lectura: `output/audit-20261111-before.json`; cierre: `output/audit-20261111-validation.json`. Se comprueban enlaces activos, correspondencia de la cola, hashes de archivos de implementación y tablas protegidas. No se repiten suites de aplicación por cambios exclusivamente documentales.

Resultado del cierre: **25 entradas/138 enlaces locales correctos, 318 archivos de implementación sin cambios y 13 tablas protegidas/18 modelos idénticos**. No se modificó la aplicación ni sus permisos. El recuento inicial auxiliar de ciclos consultó un nombre de tabla inexistente; la evidencia final usa `automation_cycles` y confirma los cinco resultados PARTIAL, sin atribuir ausencia a n8n.

Invariantes conservados: coste obligatorio 0 EUR, PAPER ONLY, `POST /api/orders=403`, MASTER ficticio separado y P4 PARTIAL. La reorganización no activa minería real, riesgo ni ejecución. [Decisión D045](../../DECISIONES.md).
