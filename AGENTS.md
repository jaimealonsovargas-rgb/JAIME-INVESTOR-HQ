# Instrucciones permanentes para Codex

## Invariantes no negociables
1. Coste obligatorio de servicios igual a **0 EUR**. No crear infraestructura facturable ni compras de créditos.
2. **PAPER ONLY**: nunca enviar órdenes a endpoints live ni usar fondos reales. Defensa en profundidad en código y tests.
3. La pantalla inicial es el **mundo 3D jugable en tercera persona**, no un dashboard ni una vista aérea. Los nueve departamentos son espacios reales conectados, con pantallas clicables. El usuario controla un avatar humano visible y la cámara principal le sigue desde atrás, ligeramente elevada, a escala humana. Las cámaras panorámicas/isométricas solo son auxiliares para inspección o mapa, nunca la perspectiva de juego predeterminada.
4. No inventar cotizaciones, trades, beneficios, trabajos de agentes, resultados de tests, disponibilidad de APIs o licencias.
5. Ledger maestro de **10.000 EUR ficticios** separado de cuentas paper de brókeres; sin doble conteo.
6. Cada fase exige tests, revisión de seguridad, evidencia visual cuando corresponda y actualización de STATUS.md.
7. Secretos solo en .env local; nunca en frontend, logs, capturas, repositorio o prompts.
8. Fuentes y modelos 3D gratuitos con licencia comprobada y atribución registrada.
9. Español para interfaz y comunicación; identificadores de código pueden ser ingleses.

## Regla permanente de perspectiva jugable (P1.C–P7)
- Diseñar, implementar y probar cada departamento **desde la cámara de seguimiento detrás del avatar**, no optimizar únicamente capturas panorámicas de P1.B.
- Avatar humano visible en pantalla; cámara a unos metros detrás y algo por encima del personaje, orientada hacia donde avanza, con seguimiento suave, giro por ratón y zoom limitado. Evitar cámara cenital, isométrica fija o primera persona como modo principal.
- Resolver colisiones y oclusión entre cámara, techo, paredes acristaladas, mobiliario y avatar. Las puertas, pasillos y monitores deben ser usables a escala humana y desde la posición real del jugador.
- Las capturas de aceptación y pruebas de FPS de P1.C en adelante deben mostrar **avatar + vista de juego en tercera persona** y desplazamiento real; la vista de planta es solo evidencia complementaria.
- Ver especificación completa en `docs/02_MUNDO_3D.md` y `tasks/P1_OFICINA_3D.md`.

## Protocolo de ahorro de tokens
- Leer docs/00_INDICE.md y el ticket activo; abrir **solo los documentos relevantes**.
- Trabajar una fase o sub-tarea acotada por turno; no cargar todo el repositorio sin necesidad.
- Preferir diffs y cambios locales; no reescribir módulos estables ni pegar archivos completos en respuestas.
- Guardar decisiones, tests, bloqueos y siguiente paso en STATUS.md.
- Selección **manual** de modelo por el usuario: Sol Medio para rutina; Sol Alto para 3D; Astra Alto para arquitectura, finanzas críticas y auditorías. Ver docs/18_MODELOS_Y_TOKENS.md.
- Escalar solo el problema difícil y regresar a Sol después; evitar agentes paralelos masivos y modo de consumo acelerado.

## Protocolo de ejecución
Inspeccionar → plan breve → implementar → pruebas → revisión visual/financiera → actualizar STATUS → resumen. Si algo no funciona o no está autorizado, mostrar motivo y marcar NO DISPONIBLE. Nunca fingir una integración o una operación.

## Seguridad operativa
La IA nunca controla directamente órdenes ni excepciones al riesgo. El motor determinista de riesgo y el kill switch mandan siempre. UNKNOWN en una orden de bróker significa reconciliar antes de cualquier reintento.
