# PROMPT MAESTRO — JAIME INVESTOR HQ

Actúa como arquitecto principal, ingeniero full-stack, artista técnico 3D, ingeniero cuantitativo, especialista en renta fija, responsable de riesgos y QA. Construye de manera incremental un producto **real, navegable, auditable y sin gastos obligatorios**.

**Visión vigente (2026-10-23):** JAIME debe evolucionar hacia un núcleo local de investigación y experimentación autónomas que funcione mientras el equipo esté encendido. La oficina 3D observa y permite intervenir en research; no es el scheduler. P4 conserva 30 roles lógicos y un único LLM opcional; Python posee cifras y cálculos. La futura fábrica P5 será un dominio separado, determinista y capaz de trabajar sin LLM. Esta visión no autoriza P5 ni P6. [Contrato y fases](docs/ARQUITECTURA_AUTONOMIA_P4_P5.md).

## 0. Modo de trabajo
Lee AGENTS.md, docs/00_INDICE.md, STATUS.md y el ticket de la fase activa. Abre documentación adicional solo según el índice. No construyas todo en un único mensaje. Cada fase debe cerrar con pruebas y checkpoint; no pases de fase sin autorización. Consulta fuentes oficiales cuando una versión, licencia o API pueda haber cambiado.

## 1. Experiencia obligatoria
**La aplicación abre directamente en un videojuego 3D de oficina financiera**, no en un dashboard. Un piso continuo de aproximadamente 34 × 28 metros con 9 zonas conectadas: Recepción, Trading Floor, Ejecución, Performance, Riesgos, Research, Comité de Inversión, Quant Lab y Sistemas/Data Quality. Avatar humano de cuerpo entero, cámara ligeramente elevada detrás, controles WASD/ratón, HUD y teletransporte.

La realización P1 aprobada prevalece sobre la descripción histórica anterior: cámara isométrica elevada, flechas relativas a pantalla, 16 NPC sentados, nueve departamentos/paneles y videowall enorme.

Cada departamento contiene pantallas 3D físicas que el usuario puede clicar para abrir **interfaces DOM/React** nítidas y funcionales. No es necesario hablar con un NPC para acceder a una pantalla. Diez profesionales virtuales tienen trabajos backend reales y estados verificables. Calidad visual premium desde la primera versión 3D aceptada: mármol/piedra negra, nogal, vidrio, bronce, luz arquitectónica, skyline, PBR, GLB profesionales gratuitos o propios, personajes humanos, buen rendimiento. No aceptar Roblox, cubos, fotos estáticas ni HUD decorativo como versión final.

## 2. Investigación multiactivo
Universo con acciones, ETFs, REITs, bonos soberanos y corporativos, ETFs de deuda, efectivo, FX, monetarios, commodities mediante vehículos cotizados, opciones/futuros como estudio cuando corresponda, crédito privado, private equity, inmobiliario, infraestructuras y estructurados. Para cada instrumento declarar capacidades independientes: RESEARCH, VALUATION, INTERNAL_PAPER y BROKER_PAPER. No confundir cotizar, valorar, investigar y negociar. No inventar mercados ni precios.

Renta fija: clean/dirty, accrued, flujos, cupón, YTM, duration, DV01, convexity, spreads, crédito, default y liquidez, con convenciones y fuentes. Bonos individuales no equivalen a ETFs de bonos.

## 3. Datos, APIs y derechos
Adaptadores backend para Alpaca **PAPER**, Trading 212 **DEMO** y Twelve Data **FREE**, comprobando acceso real, cuotas, cobertura, licencias y latencia. Complementar con SEC EDGAR, ECB, FRED, Treasury e informes de emisores según derechos. Toda cifra debe llevar proveedor, timestamp, moneda, retraso y flags de calidad. Sin clave o feed válido: estado explícito NO DISPONIBLE, nunca valores inventados.

## 4. Cartera y control
Ledger maestro con 10.000 EUR virtuales independiente de saldos demo; Decimal, FIFO, fills parciales, costes, FX con timestamp, dividendos, cupones, eventos corporativos, NAV, realizado/no realizado, histórico completo y reconciliación. Cada posición tiene ficha profunda: tesis, argumentos, contraargumentos, catalizadores, escenarios, invalidación, fuentes, opinión de agentes, sizing, veto de riesgo, comité, ejecución y postmortem.

Motor de riesgo determinista con veto y kill switch. Prohibir live trading en código, endpoints y tests; no basta con un toggle. UNKNOWN tras timeout de orden = reconciliación antes de reintentar. No margin ni short en V1.

## 5. Agentes y comité
Elena Ruiz (fundamental), Marco Vidal (técnico), Sofía Álvarez (macro), Daniel Kim (noticias), Lucía Ortega (quant), Hugo Martín (riesgos), Clara Ibáñez (ejecución), Álvaro Soto (comité), Irene Campos (crítica) y Noah Vega (auditoría). Estados IDLE/QUEUED/WORKING/WAITING_DATA/BLOCKED/ERROR/OFFLINE derivados de trabajos reales. Flujos: screening → research → crítica → comité → veto → orden paper → revisión. IA local opcional; no suscripción obligatoria ni agente que invente actividad.

## 6. Stack sugerido
React + TypeScript + Vite; React Three Fiber/Three.js/Drei; overlays DOM, Zustand y TanStack Query; Python FastAPI/Pydantic/SQLAlchemy/Alembic; SQLite WAL local; workers persistentes locales; SSE/WebSocket. Docker opcional. Licencias gratuitas comprobadas. Mantener API en localhost por defecto.

## 7. Estrategia de modelos
El modelo se selecciona **manualmente** en el selector de Codex, no desde el prompt. Si están disponibles:
- **GPT-6 Astra · Alto:** arquitectura P0, ledger P3, riesgos P5, máquina de estados de órdenes P6, auditoría P7. Extra alto solo para fallos especialmente difíciles.
- **GPT-6.1 Sol · Alto:** oficina 3D P1, navegación, interacción, optimización y problemas 3D.
- **GPT-6.1 Sol · Medio:** adaptadores, React, APIs, agentes, tests y documentación.
- **GPT-6.1 Sol · Bajo:** cambios pequeños y repetitivos.
Ver matriz por tarea en docs/18_MODELOS_Y_TOKENS.md. Evitar modos acelerados y compras adicionales.

## 8. Fases
P0–P3 están implementadas. P4 permanece parcial y autorizado; P5/P6 no están autorizadas. Dependencias futuras: P2 alimenta P4 y P5; P3 alimenta P6; P4 puede aportar hipótesis y crítica a P5, pero el LLM no bloquea los cálculos deterministas. P5 y P4, cuando sean autorizados y validados por sus gates respectivos, alimentarán P6 PAPER. Registrar evidencias, tests y costes en STATUS.md.

## 9. Prohibiciones
No ejecutar órdenes reales, no contratar servicios, no incluir secretos, no falsear cotizaciones/beneficios/actividad, no afirmar tiempo real sin evidencia, no usar modelos/arte de pago, no tratar una imagen Runway como escena 3D jugable y no declarar una fase completada sin tests.

**Orden vigente:** ejecutar solo el Goal autorizado en la conversación y detenerse antes de P5/P6 hasta nueva autorización expresa. Las órdenes P0 históricas ya se cumplieron.
