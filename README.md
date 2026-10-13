# JAIME INVESTOR HQ

**Oficina 3D jugable de un fondo de inversión virtual multiactivo.**

**Estado:** especificaciones, documentación y tareas para Codex. **NO es aún una aplicación funcional.**  
**Capital inicial:** 10.000 EUR virtuales. **Órdenes:** exclusivamente PAPER/DEMO. **Gasto obligatorio de servicios:** 0 EUR.

## Cómo abrir la carpeta

1. En este repositorio, pulsa **Code → Download ZIP** y descomprímelo; alternativamente, clónalo con GitHub Desktop o Git.
2. En **Visual Studio Code**, selecciona **Archivo → Abrir carpeta → JAIME-INVESTOR-HQ**.
3. Instala la extensión oficial de **Codex** e inicia sesión.
4. Lee AGENTS.md, CODEX_MASTER_PROMPT.md, docs/00_INDICE.md y STATUS.md.
5. En Codex, selecciona **GPT-6 Astra, razonamiento Alto**, si está disponible. Envíale el mensaje de **CODEX_START_HERE.md**. La primera tarea es **P0**, no toda la aplicación.
6. Para la fase 3D, cambia manualmente a **GPT-6.1 Sol, razonamiento Alto**, si aparece en tu selector.

## El producto

La aplicación abre **directamente dentro de la oficina 3D**; nunca en un dashboard plano. Una sola planta, cámara elevada en tercera persona, avatar humano, nueve departamentos, diez NPC profesionales, pantallas físicas clicables que abren interfaces financieras React nítidas y navegación WASD/teletransporte. Calidad arquitectónica premium desde la primera fase visual aceptada.

Las funciones incluyen: universo multiactivo; análisis fundamental, técnico, macro, crédito y cuantitativo; comité; riesgos con veto; posiciones y órdenes; P&L EUR; historial de cada operación; tesis, evidencias y postmortems; integraciones paper con Alpaca/Trading 212 y datos de Twelve Data cuando sus condiciones lo permitan.

## Carpetas

- AGENTS.md — reglas permanentes de Codex, seguridad y ahorro de contexto.
- CODEX_MASTER_PROMPT.md — visión completa y criterios de construcción.
- CODEX_START_HERE.md — primer mensaje que pegar en Codex.
- docs/ — diseño, instrumentos, renta fija, proveedores, contabilidad, agentes, riesgo, modelos, pruebas y auditoría.
- tasks/ — fases P0 a P7 con condiciones de salida.
- assets/ — plano SVG, paleta y referencias a imágenes de Runway.
- .env.example — nombres de variables; nunca valores reales.
- STATUS.md — progreso y pruebas, actualizado por Codex.

## Límites

No hay ejecución real, ni garantías de feeds profesionales en tiempo real para todos los activos, ni servicios remotos 24/7 con el ordenador apagado. Las imágenes conceptuales de Runway no son archivos 3D ni la aplicación terminada. Codex puede estar sujeto a límites de uso del plan existente. No activar recursos de pago sin autorización.

**Siguiente paso: ejecutar solo tasks/P0_BASE.md, comprobar tests y revisar el resultado antes de P1.**
