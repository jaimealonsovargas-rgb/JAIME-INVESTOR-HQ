# B4 · Validación y selección de estrategias

19 de noviembre de 2026. El selector revisó los diez ensayos registrados de BRK.B/IEX. Las tres medias móviles quedaron descartadas. B5 recibe `NO_CANDIDATES`, una lista vacía y la acción `OBSERVE`. La campaña lleva 60 sesiones de calentamiento y 192 de evaluación. Las 252 forman parte de la exposición previa. [Campaña B3.2](ENTREGA_B3_2.md) · [Mandato B4 archivado](../archive/2026-11-19-b4/ACTUAL.md).

## Criterios y evidencia privada

El informe privado desglosa las medias móviles de 20, 40 y 60 sesiones frente a los controles de efectivo y comprar y mantener en cada escenario.

El criterio original exigía superar estrictamente a ambos controles después de costes y limitar la caída máxima a la de comprar y mantener. Cada variante conserva su configuración, sus métricas en ambos escenarios y sus motivos de descarte. El expediente privado incluye las rentabilidades, las caídas, el número de operaciones, los costes y la rotación bruta sobre el capital inicial. La sensibilidad se muestra como diferencia de rentabilidad entre costes y como rango de resultados entre parámetros de la misma familia. [Protocolo económico original](B3_2_PROTOCOLO_v1.json).

El activo se eligió después del periodo y el histórico incluye la información revisada que se conocía al preparar la campaña. El intervalo del 30-12-2024 al 31-12-2025 quedó observado, inclusive para descendientes de esas hipótesis. Hay **cero sesiones reservadas**. La evidencia estadística de las tres variantes es `INSUFFICIENT_EVIDENCE` y el valor p figura como nulo. Las tres son variaciones de una sola familia de tendencia en un único instrumento.

## Contrato de validación v1

1. El adaptador abre SQLite en modo de lectura y obtiene los datos, ensayos y eventos de una sola transacción. Contrasta el registro completo con el grid declarado, el informe B3.2 sellado, el manifiesto, los hashes de código, configuración y resultados, y las evidencias de calendario. Comprueba el registro de todos los ensayos antes del primer cálculo, los reintentos, el calentamiento sin operaciones, la hora de cada decisión y su relación con las ejecuciones simuladas. La fecha del cierre anterior es una hipótesis del simulador de B3.2.
2. El selector cuenta cada hipótesis declarada y conserva también los ensayos fallidos, rechazados y de control. Identifica la exposición registrada por instrumento a través de campañas, nombres y hashes de datasets. El alcance del inventario real es el registro quant local. En el contrato prospectivo se incorporan los instrumentos heredados y se veta cualquier intersección con las ventanas protegidas.
3. Una futura campaña confirmatoria necesita un protocolo verificable registrado antes de abrir la primera validación. Su hash fija las hipótesis, costes, controles, alcance, particiones y política de selección. El contrato admite varios tramos sucesivos de entrenamiento y validación con una reserva final de un solo uso. Comprueba orden, días de purga por horizonte, embargo y cartera plana al entrar en cada ventana puntuada. Esta versión exige el registro antes del día de la primera validación y la apertura de la reserva después de su último día UTC.
4. Los mínimos de ingeniería de v1 son 126 sesiones de entrenamiento, 63 por tramo de validación y 126 para la reserva final. Se fijaron para el uso prospectivo. Para realizar inferencia se exigen además datos conocidos a su fecha, inventario de exposición acreditado y evidencia revisada de que procede una prueba de signos sobre bloques. Las ventanas y los supuestos se ilustran con datos de prueba. El único adaptador real de esta entrega es el de B3.2.
5. En una reserva admisible, se comparan las rentabilidades netas emparejadas en bloques completos de diez sesiones contra ambos controles, en cada escenario. Se exigen al menos doce bloques. Los empates cuentan como resultados no favorables y las sesiones sobrantes entran en las métricas económicas. La prueba binomial unilateral requiere signos independientes bajo la hipótesis nula y una probabilidad de victoria por bloque como máximo de 0,5. Se toma el mayor valor p entre controles y costes y se aplica Bonferroni al total de hipótesis preregistradas, con alfa familiar de 0,05. Este método evalúa la frecuencia de victorias por bloque. La rentabilidad neta y la caída máxima tienen sus propios criterios en cada ventana. La campaña BRK.B carece de las condiciones para realizar esa inferencia.
6. El expediente identifica series con la misma posición en cada sesión y escenario para evitar duplicar revisiones. Conserva todos los intentos en el denominador. Un candidato apto solo llega a revisión. Si falta un benchmark y ninguna variante es comparable, el resultado es `EVIDENCE_INCOMPLETE`. Una discrepancia de integridad o un registro sin cerrar genera `VALIDATION_UNAVAILABLE`, código de salida 2 y ninguna publicación nueva.

## Lectura local y trazabilidad

El 20-11 se verificó también el mismo expediente con una vista limitada para el generador (`--format proposer`). La revisión añadió un piloto de optimización separado con datos de ingeniería. [Evaluación y resultados](MINERIA_REPOS_2026_11_20.md).

El expediente canónico es `output/strategy-validation/5b3f92b437746935f3a4d58991c84962e5f1f2dd7f774083659b66fbe5a35421.json`. El resumen legible de esta entrega está junto a él en el archivo del mismo nombre con extensión `.md`. Ambos son privados. El contenido canónico guarda agregados y referencias a los ensayos originales. El informe conserva los identificadores de la política, implementación, campaña, dataset, universo, manifiesto y revisión.

Para abrir el informe archivado en la terminal de JAIME, incluso después de vencer la revisión interna de los datos, se puede ejecutar el siguiente comando.

```powershell
.\.venv\Scripts\python.exe scripts/validate_strategies.py --show 5b3f92b437746935f3a4d58991c84962e5f1f2dd7f774083659b66fbe5a35421 --format markdown
```

El comando sin argumentos vuelve a validar localmente durante la vigencia de la revisión y publica el JSON por contenido con el control de espacio de JAIME. Dos ejecuciones devolvieron el mismo identificador. El consumidor de B5 puede leerlo con `ValidationStore.read(id)` y comprobar la decisión, la lista de candidatos y la acción. El ID se toma de la entrega verificada. Un archivo que no supera la comprobación de integridad detiene la lectura.

## Comprobaciones

- **168 pruebas aprobadas**, incluidas 57 de B4, más las regresiones de admisión, manifiestos y laboratorio. Se probaron la exposición heredada, los límites temporales, los costes adversos, los empates, el registro incompleto, la manipulación de métricas y las publicaciones repetidas.
- Una prueba aritmética recorrió **500 variantes y 1.004 ensayos de prueba**. Las cuatro ejecuciones de control corresponden a efectivo y comprar y mantener con dos costes. La corrección por las 500 hipótesis evitó aceptar el resultado del ejemplo. Esta prueba mide el comportamiento del selector. La evidencia con precios reales sigue siendo la campaña de diez ensayos.
- Las cuatro tablas contables de MASTER, las tres del laboratorio y la tabla de versión de Alembic conservaron sus recuentos y hashes en la base local antes y después de la validación. La prueba de la API confirmó HTTP 403 para `POST /api/orders`. Schema `0015_history_batches`, PAPER ONLY, coste externo 0 EUR y P4 PARTIAL.

El siguiente bloque del proyecto es B5, autonomía y riesgo. Su entrada real en este punto es observación. [Ficha activa](../../tasks/ACTUAL.md) · [Hoja de ruta](../../tasks/ROADMAP.md).
