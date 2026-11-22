# n8n local — B2.5

Versión verificada: n8n Community **2.46.6**, Node **24.22.1**, Windows, 06-11-2026. Uso personal/local conforme a la Sustainable Use License; no se requieren licencia Enterprise ni servicios facturables. Manifiesto y lock de esta carpeta fijan el runtime. [Instalación oficial](https://docs.n8n.io/hosting/installation/npm/), [CLI](https://docs.n8n.io/hosting/cli-commands/), [licencia](https://github.com/n8n-io/n8n/blob/n8n%402.46.6/LICENSE.md).

## Uso habitual

Desde la raíz del proyecto, con el backend y la interfaz arrancados:

```powershell
.\.venv\Scripts\python.exe scripts/n8n_shadow.py start
```

Al aceptar una ventana, JAIME verifica el expediente B4 y registra la decisión B5 en la misma transacción. Un reintento recupera su comprobante. La revisión de riesgo permanece accesible aunque falle después una descarga SEC. [Motor y controles B5](../../docs/actual/ENTREGA_B5.md).

El flujo publicado revisa Apple, Microsoft y Walmart a las **00:00, 06:00, 12:00 y 18:00 UTC**. En Madrid cambia la hora local con el horario de verano; el panel muestra la fecha convertida. Son ventanas de revisión documental, no horarios de sesión bursátil. El planificador omite ventanas perdidas; no ejecuta una campaña de recuperación al encender el ordenador.

Control habitual en [Sistemas → Casos y entregas](http://127.0.0.1:5173/?especialista=personal-systems): pausar nuevas solicitudes, permitirlas de nuevo y cancelar un ciclo activo. Permitir solicitudes no arranca el proceso de n8n. Ambos servicios y el ordenador deben estar encendidos; no se ha creado un servicio de inicio automático de Windows.

Si el reloj del equipo avanza durante una suspensión, comprueba la fecha del último ciclo en Sistemas. La agenda omite las ventanas vencidas. El disparador manual «Comprobar ventana actual» del flujo permite solicitar la vigente y recuperar su recibo si ya existe.

El editor n8n está en `http://127.0.0.1:5678`. Su cuenta local de editor no se ha configurado; el flujo ya está importado y publicado por CLI. La supervisión del piloto se hace desde JAIME. No abrir puertos, túneles ni introducir claves de Alpaca en n8n.

## Preparación reproducible

La preparación ya está hecha en este equipo. Para reconstruir otra instalación local con Node compatible, crear `.tools/n8n` y copiar allí `package.json` y `package-lock.json` de esta carpeta; ejecutar `npm ci --prefix .tools/n8n --ignore-scripts --no-audit --no-fund`. Los scripts opcionales de instalación de dependencias no forman parte del piloto verificado.

```powershell
.\.venv\Scripts\python.exe scripts/n8n_shadow.py prepare --node C:/ruta/a/node.exe
.\.venv\Scripts\python.exe scripts/n8n_shadow.py publish
.\.venv\Scripts\python.exe scripts/n8n_shadow.py start
```

`prepare` copia el ejecutable indicado a `.tools/n8n-node/node.exe`, genera claves independientes en `.env` si faltan, valida las expresiones con el parser de la versión instalada e importa la credencial cifrada y el flujo. No muestra claves. La importación usa un archivo temporal que se retira incluso si falla. Conservar **N8N_ENCRYPTION_KEY** junto con el respaldo privado de `data/n8n`; sin ella no se pueden recuperar las credenciales cifradas. No volver a preparar un workflow activo sin planificar su parada: la importación puede cambiar su publicación.

Con n8n detenido, `scripts/n8n_shadow.py run` ejecuta el mismo flujo para la ventana actual. Repetirlo recupera el mismo ciclo. `unpublish` retira su publicación. Las modificaciones de publicación por CLI requieren reiniciar n8n si está encendido. No ejecutar a la vez el CLI de ejecución y el servidor: comparten el puerto local del runner.

## Límites de esta instalación

- Binding exclusivo `127.0.0.1`: editor 5678, runner interno 5679. Sin Redis, workers distribuidos ni acceso a brokers. API pública, telemetría, catálogo de plantillas y paquetes comunitarios desactivados.
- Solo se cargan Manual Trigger, Schedule Trigger, HTTP Request, Wait e If. El flujo no usa nodos Code, ejecución de comandos, lectura de archivos, LLM ni URLs suministradas por eventos.
- La credencial HTTP solo permite el contrato de ciclos de JAIME. Se guarda cifrada en n8n; las claves originales permanecen en `.env`. El proceso de n8n no hereda las claves de proveedores.
- Las respuestas contienen IDs, estados y referencias de modelos; ningún corpus de cuentas ni precios. Guardado de datos de ejecuciones desactivado y poda de metadatos a siete días/1.000 ejecuciones; JAIME conserva el registro canónico. Los logs privados de la prueba CLI sí contienen esos metadatos.
- Instalación medida: 2.090.542.249 bytes de paquetes y 93.713.712 bytes del ejecutable Node, aproximadamente **2,18 GB**, más base n8n y caché compartida npm. No son datos de empresas. No se ha borrado caché global ni historial del usuario.
- Desde el 07-11 se desactiva además el módulo opcional `mcp-registry`: evita su consulta periódica al catálogo externo, ajena al piloto. La lista de nodos permitidos sigue limitada a los cinco tipos anteriores. El runtime advierte de un runner Python ausente y de futuras deprecaciones de instalación; este flujo no usa Python ni Code en n8n. Su revisión corresponde a una actualización controlada del pin, no a habilitar herramientas adicionales.

Contrato, pruebas y resultado real: [entrega B2.5](../../docs/actual/ENTREGA_B2_5.md).
