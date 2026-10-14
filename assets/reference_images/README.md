# Referencias originales aprobadas — importación segura

**Estado:** los PNG originales se encuentran en el ZIP de handoff proporcionado en la conversación. **No confundir el SVG del plano con los PNG aprobados.** Si los PNG aún no están aquí, el repositorio no contiene todavía la referencia original a resolución completa.

**Imagen principal**: JAIME_HQ_SIMS_VIDEOWALL_APROBADA.png (1672×941), oficina isométrica minimalista tipo Los Sims, videowall gigante arriba, SHA-256 `4e07c5f1ea91b598ce8e3fcbcc1e73da6332b64006f8c03a21df7fa7a515ef92`.

**Imagen secundaria**: JAIME_HQ_SIMS_BASE.png (1672×941), oficina Sims anterior sin gran pantalla, SHA-256 `69101f7a18a0d48908b3e3a060e64ffeb1c89a2a975ccb085ac9bdf6dfd83347`.

## Para Codex — cuando el ZIP esté en el workspace

1. **No detener la implementación en curso.** Completar checkpoint, conservar trabajo local.
2. Colocar el archivo **JAIME_HQ_REFERENCIAS_Y_HANDOFF.zip** en la raíz del repo. Si está en otra ubicación, indicar su ruta al script.
3. Ejecutar: `python scripts/import_approved_references.py` o `python scripts/import_approved_references.py "C:\\ruta\\al\\ZIP"`.
4. El script extrae **solo dos PNG**, verifica hashes y no sobrescribe ficheros diferentes. No hace git pull/push/commit ni modifica código.
5. Después comprobar `git status --short`, `git add assets/reference_images/JAIME_HQ_SIMS_VIDEOWALL_APROBADA.png assets/reference_images/JAIME_HQ_SIMS_BASE.png`, y hacer commit seguro según el flujo LOCAL.
6. La imagen aprobada es la **PRINCIPAL con videowall**. El SVG es solo referencia espacial secundaria.

[Manifiesto](../REFERENCIA_APROBADA_MANIFIESTO.md) · [Especificación completa](../../docs/ESPECIFICACION_DEFINITIVA_2026_10_15.md) · [Prompt Codex](../../docs/PROMPT_CODEX_EJECUCION_COMPLETA_P1_P2.md).
