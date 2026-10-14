# Instrucciones permanentes para Codex

## Invariantes no negociables
1. Coste obligatorio de servicios igual a **0 EUR**. No crear infraestructura facturable ni compras de créditos.
2. **PAPER ONLY**: nunca enviar órdenes a endpoints live ni usar fondos reales. Defensa en profundidad en código y tests.
3. La pantalla inicial es el **mundo 3D jugable en tercera persona**, no un dashboard ni una vista aérea. Los nueve departamentos son espacios reales conectados, con nueve monitores físicos y nueve paneles React activados al acercarse al agente principal sentado de cada departamento. El usuario controla un avatar humano visible y la cámara principal le sigue desde atrás, ligeramente elevada, a escala humana. Las cámaras panorámicas/isométricas solo son auxiliares para inspección o mapa, nunca la perspectiva de juego predeterminada.
4. No inventar cotizaciones, trades, beneficios, trabajos de agentes, resultados de tests, disponibilidad de APIs o licencias.
5. Ledger maestro de **10.000 EUR ficticios** separado de cuentas paper de brókeres; sin doble conteo.
6. Cada fase exige tests, revisión de seguridad, evidencia visual cuando corresponda y actualización de STATUS.md.
7. Secretos solo en .env local; nunca en frontend, logs, capturas, repositorio o prompts.
8. Fuentes y modelos 3D gratuitos con licencia comprobada y atribución registrada.
9. Español para interfaz y comunicación; identificadores de código pueden ser ingleses.

## Regla permanente de perspectiva jugable (P1.C–P7)
- Diseñar, implementar y probar cada departamento **desde la cámara de seguimiento detrás del avatar**, no optimizar únicamente capturas panorámicas de P1.B.
- Avatar humano visible en pantalla; **cámara claramente por encima de la cabeza del personaje** (tercera persona elevada, estilo videojuego), situada a unos metros detrás y orientada hacia donde avanza. Como punto de partida ajustable: altura de cámara aprox. 2,8–3,8 m sobre el suelo para un avatar de ~1,75 m y separación horizontal de 3–4,5 m. Debe verse bien el avatar entero y parte del suelo por delante, con seguimiento automático suave, sin giro manual de cámara: ↑/↓ desplazan al personaje y ←/→ giran su rumbo. No usar cámara cenital, isométrica fija ni primera persona como modo principal.
- Resolver colisiones y oclusión entre cámara, techo, paredes acristaladas, mobiliario y avatar. Las puertas, pasillos y puestos de agentes principales deben ser accesibles a escala humana y desde la posición real del jugador.
- Las capturas de aceptación y pruebas de FPS de P1.C en adelante deben mostrar **avatar + vista de juego en tercera persona** y desplazamiento real; la vista de planta es solo evidencia complementaria.
- Ver especificación completa en `docs/02_MUNDO_3D.md` y `tasks/P1_OFICINA_3D.md`.

## Prioridad vigente: revisión P1 + P2 (2026-10-14)
- Juego normal **solo flechas** para navegar; no WASD ni ratón para orientar la cámara. Cámara de seguimiento automática, elevada, detrás del avatar; ratón reservado a interfaces DOM.
- **9 monitores físicos + 9 paneles**, abiertos automáticamente por proximidad al agente principal de la sala; no E/clic obligatorios. Histéresis para evitar reapertura tras cerrar. **10 NPC profesionales sentados** con animaciones de trabajo puramente ambientales: agentes IA reales P4 aún NO DISPONIBLES.
- Recepción sin sofás; cristales sin bloqueo de paso; Performance y Sistemas redistribuidos; mejor caminar/iluminación/calidad sin degradación grave Intel.
- Excepción de alcance expresamente autorizada: **corrección final P1 + inicio P2 en una ejecución con gates separados**, siguiendo `docs/PLAN_EJECUCION_P1_P2.md` y `docs/PLAN_P2_CHECKPOINTS.md`. STOP antes de P3. Preservar el código LOCAL.

## P2 — conectividad máxima viable (petición posterior del usuario)

- **No limitar P2 a siete fuentes.** Seguir el catálogo [docs/P2_CATALOGO_MAXIMO_FUENTES.md](docs/P2_CATALOGO_MAXIMO_FUENTES.md): **34 candidatas** (19 públicas, 15 con registro o gratuitas condicionadas), más fuentes oficiales especializadas.
- Priorizar integraciones públicas sin clave, **activación bajo demanda** con cache/cuotas y derechos verificados. Preparar conectores opcionales con clave, sin registrarse ni comprar por el usuario. Diferenciar **candidata / implementada / conectada real / utilizable**. No declarar conexión solo por mock.
- Si un proveedor falla, registrar motivo y continuar con otros. No crear decenas de stubs. Reutilizar parser/HTTP/SDMX compartidos.
- Excepción muy limitada de **POST estadístico de solo lectura** para OpenFIGI mapping y BLS v2, únicamente host+ruta+verbo allowlisted y testeados; **nunca POST a bróker, exchange, cuentas, órdenes ni trading**. Mantener POST /api/orders = 403.

## Protocolo de ahorro de tokens
- Leer docs/00_INDICE.md y el ticket activo; abrir **solo los documentos relevantes**.
- Trabajar una fase o sub-tarea acotada por turno, salvo el encargo P1 final + P2 expresamente autorizado con checkpoints; no cargar todo el repositorio sin necesidad.
- Preferir diffs y cambios locales; no reescribir módulos estables ni pegar archivos completos en respuestas.
- Guardar decisiones, tests, bloqueos y siguiente paso en STATUS.md.
- Selección **manual** de modelo por el usuario: Sol Medio para rutina; Sol Alto para 3D; Astra Alto para arquitectura, finanzas críticas y auditorías. Ver docs/18_MODELOS_Y_TOKENS.md.
- Escalar solo el problema difícil y regresar a Sol después; evitar agentes paralelos masivos y modo de consumo acelerado.

## Protocolo de ejecución
Inspeccionar → plan breve → implementar → pruebas → revisión visual/financiera → actualizar STATUS → resumen. Si algo no funciona o no está autorizado, mostrar motivo y marcar NO DISPONIBLE. Nunca fingir una integración o una operación.

## Seguridad operativa
La IA nunca controla directamente órdenes ni excepciones al riesgo. El motor determinista de riesgo y el kill switch mandan siempre. UNKNOWN en una orden de bróker significa reconciliar antes de cualquier reintento.
