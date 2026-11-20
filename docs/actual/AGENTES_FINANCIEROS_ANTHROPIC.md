# Model Builder, Earnings Reviewer y Valuation Reviewer: adaptación a JAIME

Investigación: 27-10-2026. **Recomendación de diseño, sin instalación, despliegue ni consumo de API.** Fuentes oficiales de Anthropic y su repositorio público, consultadas directamente. No se han importado prompts ni código de terceros. Se conserva el presupuesto de servicios 0 EUR.

## Qué son y cuáles corresponden a la petición

La publicación de Anthropic presenta plantillas que combinan instrucciones especializadas, conectores y trabajadores con funciones separadas. Se ofrecen para Claude y como referencias de Managed Agents; no son tres modelos financieros descargables ni un fondo que invierta automáticamente. [Anuncio oficial](https://www.anthropic.com/news/finance-agents).

El nombre oficial equivalente a “Earning Analyst” es **Earnings Reviewer**. Para “Valuation”, el agente identificado es **Valuation Reviewer**; su alcance es distinto de un creador de DCF. La valoración de cotizadas también aparece en las skills de Model Builder.

| Plantilla | Función oficial contrastada | Utilidad para JAIME |
|---|---|---|
| Model Builder | Crea modelos nuevos DCF, tres estados, comparables y LBO; inputs citados, fórmulas, auditoría y sensibilidades | Alta: cuentas normalizadas, modelo versionado, valoración y escenarios. LBO queda para otra etapa |
| Earnings Reviewer | Procesa resultados/transcript/filings, actualiza modelo de cobertura y prepara nota y variaciones | Muy alta: flujo por nuevo resultado empresarial, tabla de cambios y revisión de tesis |
| Valuation Reviewer | Revisa paquetes de valoración de gestores de fondos, NAV/allocations y reporting a inversores | Adaptación parcial: revisor independiente de supuestos/método y discrepancias. GP/LP, carried interest y administración de fondos no son prioridad de JAIME |

Fuentes por agente: [Model Builder](https://github.com/anthropics/financial-services/blob/main/plugins/agent-plugins/model-builder/agents/model-builder.md), [Earnings Reviewer](https://github.com/anthropics/financial-services/blob/main/plugins/agent-plugins/earnings-reviewer/agents/earnings-reviewer.md), [Valuation Reviewer](https://github.com/anthropics/financial-services/blob/main/plugins/agent-plugins/valuation-reviewer/agents/valuation-reviewer.md).

## Lo que conviene adoptar

Separar adquisición, construcción y revisión. El cookbook de Model Builder asigna escritura del artefacto a un solo trabajador; otro obtiene inputs y otro comprueba el resultado. El de Earnings Reviewer separa lector de texto externo, actualización y escritor, y permite derivar un cambio relevante al constructor de modelos. Esta separación es útil aunque los trabajos se ejecuten secuencialmente en un único modelo local. [Model Builder cookbook](https://github.com/anthropics/financial-services/blob/main/managed-agent-cookbooks/model-builder/README.md) · [Earnings cookbook](https://github.com/anthropics/financial-services/blob/main/managed-agent-cookbooks/earnings-reviewer/README.md).

En JAIME proponemos un flujo propio:

**NEW_FILING / EARNINGS_RELEASE → normalizador → revisión de resultados → modelo versionado → revisión de valoración → dossier/alerta → hipótesis de investigación P5.**

Se reutilizan roles `fundamental_equity`, `valuation`, `value_quality`, `data_quality` y `reporting_postmortem`, con plantillas/tipos de tarea distintos. No crear tres modelos residentes ni sumar roles nominales sin implementar entradas/salidas. Revisor en ejecución y contexto separados del constructor, sin permiso para alterar su versión; verificaciones numéricas independientes del LLM. Dos respuestas del mismo modelo no prueban independencia estadística.

### Constructor de modelos de JAIME

Entrada: snapshot normalizado, política de periodos/unidades, versión previa si existe y supuestos explícitos. Python construye tablas y fórmulas de un motor financiero tipado. Distingue valores reportados, normalizados, supuestos y proyectados. Produce `FinancialModelVersion`, controles contables, escenarios y sensitividades; Excel opcional como exportación, no base de datos ni requisito de ejecución.

Primer alcance: tres estados y DCF/comparables sencillos cuando los inputs estén disponibles. Comprobar balance, cash roll-forward, signos/unidades, deuda/caja, acciones diluidas, puente enterprise-to-equity, terminal value y sensibilidad. No calcular DCF si faltan supuestos esenciales; WACC, crecimiento o peers deben tener fuente o hipótesis etiquetada.

### Analista de resultados de JAIME

Entrada: filing/release nuevo, periodo, snapshot anterior, guidance y estimación propia fechadas antes del evento. Transcript completo solo cuando exista acceso legítimo; si falta, salida limitada a documentos disponibles, sin atribuir tono ni respuestas a una llamada no leída.

Salida: `EarningsReview` con cifras reales, comparación interanual/trimestral comparable, desviaciones frente a guidance y estimaciones propias, cambios de tesis, evidencia y propuesta de actualización. **Consenso de mercado solo con fuente autorizada y timestamp previo al anuncio**. Sin consenso, campo NO_DISPONIBLE; la proyección interna no se rebautiza como consenso.

### Revisor de valoración de JAIME

Entrada: modelo ya construido, precios/FX fechados, peers justificados y política de revisión. Salida `ValuationReview` con comprobaciones, discrepancias, sensibilidades y causa de aceptación/abstención para uso de investigación. No reescribir supuestos del constructor en silencio ni validar por estar de acuerdo con su narrativa.

Revisión de balances, coherencia de método, supuestos terminales, deuda/caja y múltiplos comparables; sectores especiales pueden requerir otro modelo. Un modelo correcto matemáticamente puede ser inadecuado para el negocio. Una valoración plausible no es una señal ejecutable ni demuestra alfa.

## Contratos y permisos

Todos los objetos incluyen `entity_id`, `instrument_ids`, `as_of`, `period`, `dataset_snapshot_id`, `source_evidence_ids`, `template_version`, `model_version`, `assumption_set_id`, `checks`, `limitations` y hash. Cada actualización guarda antes/después y motivo; no sobrescribe la historia. El evento y las tareas se deduplican por entidad/periodo/filing/versión.

Datos y documentos externos siguen siendo no confiables incluso después de convertirse a JSON: validar schema y longitud reduce superficie, pero no elimina instrucciones maliciosas ni errores. Lector sin herramientas externas/escritura, writer limitado a artefactos propios y revisor de solo lectura. El LLM no obtiene shell, órdenes, credenciales ni capacidad de cambiar políticas. Los permisos se aplican en código, no solo en prompts.

Los originales contemplan aprobación humana de artefactos o distribución. **No incorporamos esos prompts como instrucciones operativas.** JAIME tendrá una política propia compatible con el mandato: research y cálculos internos automáticos dentro de límites; resultados provisionales revisables, abstención automática si fallan gates y sin publicación externa ni ejecución. La política original de revisión humana es un diseño del proveedor, no una nueva obligación de pedir permiso en cada tarea de JAIME.

## Coste y portabilidad

Los templates se publican bajo [Apache-2.0](https://github.com/anthropics/financial-services/blob/main/LICENSE); los conectores y la ejecución Claude son capas distintas y pueden necesitar credenciales/suscripción. El [README oficial](https://github.com/anthropics/financial-services) distingue artefactos de análisis, revisión humana y acceso a proveedores. No se ha comprobado que JAIME tenga CapIQ, FactSet o Daloopa disponibles.

Recomendación: implementar los patrones y contratos en el backend existente con SEC/IR y fuentes ya autorizadas. No desplegar Managed Agents ni instalar otro stack para resolver los defectos actuales. Si en el futuro se copia material Apache, conservar licencia/atribuciones, indicar cambios y fijar revisión; este documento es análisis original y enlaces, no vendoring.

No afirmar que un modelo local compacto tendrá el rendimiento de Claude. Medir por campo/cita y abstención; usar Python y parsing determinista para lo numérico. El texto cualitativo puede ser parcial o no disponible sin bloquear cálculos válidos.

## Piloto y aceptación en B2

Tres emisores con ejercicios fiscales distintos y al menos un filing corregido; fixture sintético claramente identificado para esquinas no disponibles públicamente. Construir modelo → nueva publicación → revisión de resultados → nueva versión → revisión independiente.

- Cifras y cambios enlazan al documento/periodo exactos; ningún valor futuro se filtra al pasado.
- Balance/caja y puente EV-equity cuadran en fixtures comprobados; supuestos y cifras reportadas se distinguen.
- Dato repetido no duplica tareas; revisión legítima genera versión nueva; reinicio conserva auditoría.
- Sin consenso/transcript/modelo local, la salida explica exactamente qué falta y conserva cálculo determinista válido.
- Instrucciones dentro del documento no alteran herramientas o permisos; ningún rol modifica MASTER.
- UI permite leer Modelo, Resultados y Valoración, comparar versiones y ver crítica sin logs.

Conectar después las features fundamentales a P5 mediante datasets point-in-time y pruebas OOS. Estos tres flujos mejoran la investigación de empresas; **no implementan por sí solos la minería, el backtester, el control de selección múltiple ni la ejecución**.

Lecturas consultadas en `main` el 27-10-2026; SHA resuelto del repositorio en esa consulta: `574ed3624aebd0418c7e96cd101262f30210ab26`. Referencia para revisión posterior, no certificación de un runtime instalado.
