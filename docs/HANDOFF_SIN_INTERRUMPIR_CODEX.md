# Handoff no intrusivo a Codex en ejecución — 2026-10-15

**No detener ni reiniciar Codex**: esta actualización se hace en GitHub, **no en su working tree LOCAL**. El agente que ya está trabajando no verá necesariamente nuevos commits hasta que haga `git fetch` o lea el remoto; tampoco es seguro forzar un `git pull` si tiene modificaciones. **Nunca** `git reset --hard`, `git clean`, force-push ni sobrescribir cambios no guardados.

## Qué debe leer en su próximo checkpoint

1. [Especificación definitiva](ESPECIFICACION_DEFINITIVA_2026_10_15.md): toda la visión aprobada y precedencia.
2. [Prompt completo](PROMPT_CODEX_EJECUCION_COMPLETA_P1_P2.md): trabajo P1+P2 autorizado y STOP antes de P3.
3. [Plan maestro Sims](PLAN_MAESTRO_SIMS_VIDEOWALL_AGENTES_INTEGRACIONES.md): 9 departamentos, 16 NPC, 30 roles lógicos, videowall y terceros.
4. [Manifiesto de imagen](../assets/REFERENCIA_APROBADA_MANIFIESTO.md): hashes de PNG originales.
5. [Importador seguro](../scripts/import_approved_references.py): extraer originales del ZIP sin sobrescribir nada.

## Estado de los archivos de imagen

Los **PNG originales exactos** (1672×941, 2,63MB y 2,30MB) están en `JAIME_HQ_REFERENCIAS_Y_HANDOFF.zip`, disponible para descarga en la conversación de ChatGPT. **El ZIP no se ha subido todavía a GitHub y la conexión GitHub utilizada para editar los documentos no permite cargar directamente los binarios del contenedor.** No fingir que las imágenes están ya versionadas. En cuanto el ZIP esté en el workspace, ejecutar el importador y hacer commit de los PNG; se verifican los hashes antes de aceptar. Los SVG ya existentes en el repositorio son planos auxiliares, no sustitutos.

## Integración sin pérdida de trabajo

- No alterar el código de la sesión activa; cuando Codex complete un checkpoint, guardar y confirmar cambios locales.
- Inspeccionar `git status --short`, `git log -5 --oneline`, `git branch -vv` y divergencia con `origin/main`; hacer `git fetch` si es seguro y luego incorporar documentación con merge/rebase consciente, **nunca destructivo**.
- Si Codex no está en disposición de sincronizar ahora, **seguir trabajando** con las instrucciones ya entregadas en su prompt; podrá incorporar estos ficheros más tarde.
- Solo P1 correctivo y P2; **STOP antes de P3**. PAPER ONLY, 0 EUR, datos reales o NO DISPONIBLE.

**Esta documentación no certifica ejecución, capturas, FPS ni conectores; solo transmite decisiones y procedimiento.**
