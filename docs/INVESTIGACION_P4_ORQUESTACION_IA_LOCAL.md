# Investigación P4 — orquestación IA local, grounding y terceros

**Fecha:** 2026-10-16

## Conclusiones
1. **30 agentes no deben significar 30 LLM.** Son 30 roles lógicos con prompts, permisos y contratos diferentes; por defecto se comparte un único runtime local y se permite **1 inferencia LLM concurrente**, 2 jobs quant CPU y 4 fetches ligeros.
2. Para un PC de ~16 GB RAM e Intel integrada, la ruta razonable es un **modelo instruct compacto cuantizado**, elegido por benchmark local. No se fija un modelo por marketing: registrar nombre exacto, versión, licencia, tamaño, quant y hash.
3. El runtime debe abstraerse detrás de un adaptador `LocalLLM`. Prioridad técnica: localhost únicamente, timeout, cancelación y salida JSON con schema. `llama.cpp` ofrece servidor local con endpoints tipo Chat Completions y salida restringida por JSON/schema, útil para contratos estructurados. Fuente: https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md
4. **No usar APIs LLM facturables** en P4. Si no hay runtime/modelo local utilizable, los roles dependientes de lenguaje muestran `NO_LOCAL_MODEL`; el sistema conserva un modo determinista sin fingir análisis IA.
5. Vibe-Trading mantiene como release pública reciente `v0.1.16`; la versión auditada del repo sigue siendo metadata-only hasta revisar diff/licencia/superficie de herramientas. La release enfatiza provenance/grounding y contiene superficie de brokers/runtime que no debe habilitarse en HQ. Fuente: https://github.com/HKUDS/Vibe-Trading/releases
6. Agent Reach mantiene `v1.5.0` como release publicada. P4 solo reutiliza canales públicos/read-only ya auditados; no cookies de navegador, cuentas personales, DMs, comentarios o escrituras. Fuente: https://github.com/Panniantong/Agent-Reach/releases

## Benchmark local obligatorio
Cuando se ejecute en Windows local, probar como máximo 1–2 modelos compactos razonables para no consumir disco/RAM inútilmente. Medir:
- tiempo hasta primer token;
- tokens/s;
- pico aproximado de RAM;
- éxito de JSON/schema;
- grounding: cifras deben apuntar a `evidence_id` existente;
- seguimiento de instrucciones ante contenido externo adversarial;
- latencia de un dossier corto y de un debate Bull/Bear.

Elegir el modelo más pequeño que cumpla contratos de calidad. Si ningún candidato es usable, dejar P4 funcional en modo determinista y marcar inferencia local `BLOCKED_HARDWARE`/`NO_LOCAL_MODEL` sin inventar resultados.

## Seguridad de prompts y herramientas
- Fuentes web/RSS/social = **UNTRUSTED_CONTENT**.
- Nunca interpolar texto externo como instrucciones de sistema.
- Herramientas por allowlist y por rol; lectura P2/P3 únicamente.
- Prohibidos shell autónomo, modificación de repo, lectura de secretos, browser cookies, cuentas privadas y endpoints de órdenes.
- Un agente puede escribir solo tablas P4 de jobs/cases/evidence/results/audit; nunca ledger, fills, cash, positions o NAV.
- Cada output guarda: role/version, prompt-template version, model/runtime, input hashes, evidence IDs, timestamps, status y output hash.

## Grounding
Un dossier no debe ser un texto libre opaco. Contrato mínimo:
- resumen;
- tesis;
- supporting arguments;
- counterarguments;
- catalysts;
- risks;
- invalidation conditions;
- evidence IDs por claim importante;
- numeric claims con evidencia explícita;
- confidence cualitativa y motivos;
- unknowns/gaps;
- opiniones Bull/Bear;
- conclusión del Chair como **propuesta de research**, nunca orden.

Si una cifra o hecho no está soportado, omitirlo o marcarlo `UNVERIFIED`. Las citas rotas invalidan el claim, no se sustituyen por memoria del modelo.

## Arquitectura recomendada
`P2 data/evidence -> research case -> deterministic features -> role jobs -> LocalLLM queue (1) -> grounding validator -> Bull/Bear -> Chair synthesis -> immutable result versions -> UI/videowall`.

El scheduler es **on-demand y event-driven**, no un bucle que quema CPU/tokens continuamente. Con PC apagado no existe autonomía local 24/7; los jobs quedan persistidos y pueden reanudarse al volver a arrancar. No crear cloud de pago para resolverlo.

## Relación con fases posteriores
- P4 produce research, features descriptivos, opiniones y propuestas.
- P5 valida estrategias, backtests, riesgo determinista y veto formal.
- P6 convierte decisiones autorizadas en órdenes exclusivamente PAPER.
