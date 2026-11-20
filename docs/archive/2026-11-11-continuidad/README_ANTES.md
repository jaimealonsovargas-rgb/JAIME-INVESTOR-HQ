> ARCHIVO INACTIVO · README anterior a la auditoría, recuperado y contrastado contra su SHA-256 original. Enlaces relativos reubicados. Copia byte a byte en originals/README.md.

# JAIME INVESTOR HQ



Plataforma personal de investigación financiera y futura simulación cuantitativa autónoma, supervisada desde una oficina 3D. Objetivo: datos amplios y trazables, análisis de empresas, modelos financieros, minería de estrategias, validación y propuestas de cartera.



**Estado al 11-11-2026:** B1, B2.1 y B2.2 completados; lote contable B2.4 conciliado y B2.5 con n8n en sombra verificado. B2.3 incorpora vínculos del piloto y diagnóstico de históricos; B2 sigue abierto. Presupuesto y conservación implementados y verificados. Divisa del contrato observado documentada mediante revisión IBKR/SEC/Alpaca para las tres acciones; evidencia local y diagnóstico integrados. Próximo: identidad histórica y ampliación acotada; derechos de precios/históricos IBKR pendientes. [Operación IBKR](integrations/ibkr/README.md). P4 PARTIAL con ciclo descriptivo A21. Minería/backtests P5 todavía sin implementar. Coste obligatorio 0 EUR, MASTER 10.000 EUR ficticios y órdenes bloqueadas.



**B2.1 disponible:** Centro de activos con 8.023 emisores y 10.430 símbolos SEC, búsqueda paginada, fichas e historial local de identidad. Acceso desde la oficina o `?activos=1`. Datos de catálogo; cuentas empresariales ampliadas en B2.2, precios vinculados y modelos pendientes. [Entrega](../../actual/ENTREGA_B2_1.md).



**B2.2 disponible:** cuentas SEC de 100 emisores, informes y cifras comparativas con trazabilidad. Cola reanudable y cuadros anuales con datos ausentes explícitos. Precios Alpaca y modelos continúan en B2. [Entrega B2.2](../../actual/ENTREGA_B2_2.md).



**B2.3 disponible:** lectura Alpaca, paneles y cola recuperable; conexión real verificada el 30-10. Vínculo empresa–acción documentado para Apple, Microsoft y Walmart, con evidencia SEC y catálogo fijado. Apple conserva 21/21 sesiones IEX; Microsoft/Walmart sin histórico del piloto. Diagnóstico visible de calidad: ningún conjunto está aceptado para backtest. Divisa USD documentada para los tres contratos observados, con fecha y procedencia IBKR; continuidad histórica, escala y streaming pendientes. [Entrega de contratos](docs/actual/ENTREGA_B2_3_CONTRATOS_IBKR.md). [Lectura de mercado](../../actual/ENTREGA_B2_3.md) · [Identidad y diagnóstico](../../actual/ENTREGA_B2_3_IDENTIDAD_HISTORICOS.md).



**B2.4 disponible:** modelos versionados, ratios, comparativas y revisión numérica. Apple v7, Microsoft v5 y Walmart v6 concilian balance y caja con originales SEC; Walmart mantiene pendiente el ratio pasivos/activos. Nuevo filing real de Apple del 03-11-2026 generó v3 mediante evento idempotente; las versiones posteriores son ajustes técnicos y conservan las anteriores. DCF e interpretación local aún pendientes. [Entrega B2.4](../../actual/ENTREGA_B2_4.md) · [Day Trader: revisión y adaptación](../../actual/DAY_TRADER_ADAPTACION.md).



**Ampliación P4/Nivel 2:** 39 skills de la PR #8 incorporadas localmente; nota/tesis/calendario adaptados al ciclo existente con evidencia y abstención. Yahoo/Stooq incorporados como candidatos no oficiales, sin conexión habilitada ni derechos supuestos. [Estado y límites](../../actual/ENTREGA_B2_4_ACTUALIZACION_Y_P4.md).



**B2.5 disponible:** n8n local coordina un ciclo SEC de seis horas para tres emisores. JAIME conserva autenticación, presupuesto, cola, recuperación y modelos. Ciclos reales, reenvío y disparador automático verificados; modelos actuales Apple v7/Microsoft v5/Walmart v6, con historial preservado. Requiere el ordenador y los servicios encendidos. Panel en Sistemas → Casos y entregas. [Entrega B2.5](../../actual/ENTREGA_B2_5.md) · [Arranque de n8n](../../../integrations/n8n/README.md).



## Empezar aquí



1. [STATUS](STATUS.md): qué existe, qué falta y qué se comprobó.

2. [Trabajo siguiente B2](tasks/ACTUAL.md): universo de empresas y captación con Alpaca/SEC.

3. [Hoja de ruta única](tasks/ROADMAP.md): datos/empresas → minería → validación → autonomía/riesgo.

4. [Auditoría crítica](../../actual/AUDITORIA_2026_10_27.md): problemas concretos y evidencia.



[Visión y circuito de seis etapas](docs/actual/VISION_Y_ARQUITECTURA.md) · [Suficiencia de proveedores](docs/actual/PROVEEDORES_Y_COBERTURA.md) · [Datos y estrategias](../../actual/DATOS_Y_ESTRATEGIAS.md) · [Experiencia de producto](../../actual/EXPERIENCIA_PRODUCTO.md) · [Agentes financieros de Anthropic](../../actual/AGENTES_FINANCIEROS_ANTHROPIC.md) · [Índice](docs/00_INDICE.md).



## Arranque local



Desde la raíz, PowerShell. Setup solo para instalar/preparar entorno; preserva `.env` existente. Requisitos y versiones fijados en pyproject/uv.lock/package-lock; no descargar modelos ni crear servicios por defecto.



```powershell

python scripts/setup.py

python scripts/manage.py backend

```



En otra terminal:



```powershell

python scripts/manage.py frontend

```



Frontend: http://127.0.0.1:5173 · backend: http://127.0.0.1:8000/health · API: http://127.0.0.1:8000/openapi.json. Vite fija puerto 5173; una instancia arrancada manualmente antes en otro puerto no cambia esta configuración. La oficina conserva cámara isométrica, flechas y acceso por personas/departamentos. El backend puede investigar con la oficina cerrada mientras permanezca encendido; no funciona con el PC apagado.



## Verificación



```powershell

python scripts/manage.py check

python scripts/manage.py audit

python scripts/manage.py migrate

python scripts/manage.py portfolio-snapshot

```



`check` ejecuta backend/frontend/TypeScript/build; `audit` necesita red. `migrate` aplica migraciones existentes, no elimina base. La base personal está en data/jaime_hq.db; no borrarla para arreglar errores. Consultar contratos y procedimientos de backups vigentes antes de migrar datos personales.



## Organización



- backend/ y frontend/: aplicación; scripts/: utilidades; assets/: recursos/licencias.

- docs/actual/: dirección, auditoría y especificaciones vigentes.

- tasks/ACTUAL.md y ROADMAP.md: trabajo y aceptación; tasks/P0–P7: referencias de dominio/historia.

- docs/archive/: planes/prompts/bitácoras históricas; docs/evidencias/: pruebas de entregas anteriores.

- data/, output/, .env y entornos locales: privados/ignorados; no son basura por estar fuera de Git.



La profesionalidad se medirá por cobertura útil, temporalidad correcta, resultados auditables y experimentos reproducibles. Un número de agentes, APIs o tests no demuestra rentabilidad.

