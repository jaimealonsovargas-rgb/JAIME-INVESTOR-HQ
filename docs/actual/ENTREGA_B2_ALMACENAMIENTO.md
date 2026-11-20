# B2 — presupuesto y conservación

Entrega cerrada el 09-11-2026, Europe/Madrid. Implementación y pruebas del 08-11; cierre documental y comprobación del servicio tras reanudar. Sin migración: schema 0013. Coste obligatorio 0 EUR, PAPER ONLY, P4 PARTIAL y órdenes 403.

## Resultado

Control común antes de captar datos SEC, Alpaca, catálogo y fuentes P2, adquirir originales XBRL o construir modelos. Un bloqueo del sistema operativo serializa la unidad completa entre procesos colaboradores: comprobación de espacio, petición, archivo y commit. Una caída libera el bloqueo. No se ocupa físicamente la reserva. No es una cuota del sistema operativo ni una garantía frente a escrituras de otros programas.

| Presupuesto inicial | Límite |
|---|---:|
| data/: SQLite, WAL, SEC, mercado y datos de n8n | 4 GiB |
| output/: copias, modelos locales y resultados | 12 GiB |
| Conjunto data/ + output/ | 16 GiB |
| Margen libre mínimo de disco | 5 GiB |
| Reserva conservadora por unidad de captación | 512 MiB |

Aviso desde el 80%. Se comprueban tamaños lógicos, WAL incluido, antes de cada unidad; los límites anteriores de 500.000 barras, 512 MiB de originales de mercado y 10.000 versiones de modelos siguen vigentes. La reserva no acredita que cualquier carga futura quepa: los nuevos adaptadores deben revisar su amplificación de datos y memoria antes de usarse. No habilita captación masiva.

Configuración documentada en `.env.example`, campos STORAGE_*, requiere reiniciar backend. No se modificaron secretos ni valores del `.env` personal. Los entornos, dependencias y aplicaciones externas no pertenecen a esa cuota de captación; su consumo sí reduce el espacio libre del disco.

## Medición e inventario

Inventario privado `output/storage-inventory-20261108.json`: unos 558,7 MiB en datos y 7,42 GiB en output; 7,96 GiB conjuntos. En output destacan 5.047.045.396 bytes de runtime/modelos P4 y 2.552.733.696 bytes de archivos de base de datos clasificados como copias (incluye bases de pruebas, no todas son respaldos personales). Los tres GGUF grandes suman aproximadamente 4,63 GiB. No se borró ninguno.

Una copia visual antigua enlaza las dependencias de frontend mediante una junction. Se reconoce únicamente el destino de runtime conocido y se cuenta aparte, evitando duplicar unos 254 MiB. Enlaces desconocidos o errores en datos/output bloquean la admisión. El inventario de `.tools` registra una ruta anidada inaccesible en el paquete n8n: su tamaño es parcial, con un error explícito; no se presenta como inventario completo del ordenador ni se reinstaló el runtime.

El manifiesto contiene rutas relativas, tamaños y fecha de modificación, todos con PRESERVE. Es un inventario de conservación, **no autorización ni plan ejecutable de borrado**. No incluye cuerpos de documentos ni secretos. Para otro informe, usar un nombre nuevo:

```powershell
.venv/Scripts/python.exe scripts/storage_inventory.py --output output/storage-inventory-NUEVA-FECHA.json --include-runtimes
```

## Política de conservación

| Dominio | Política vigente |
|---|---|
| Ledger, cartera MASTER | Append-only; sin limpieza automática. |
| Originales SEC/mercado, recibos y XBRL | Conservar evidencias y referencias. Original idéntico reutiliza hash; revisión nueva conserva anterior. |
| Snapshots, hechos, revisiones y barras | Conservar historia y fechas de conocimiento; detener nuevas unidades al límite. |
| Modelos contables y entregas de investigación | Conservar versiones, inputs y evidencias; no reconstruir para liberar espacio. |
| Copias de seguridad y modelos GGUF | Conservar. Una futura reubicación necesita inventario con hashes, validación de referencias y restauración probada. Una copia en el mismo disco no protege contra fallo físico del disco. |
| Caché P2 | Se mantiene su TTL y máximo existente de 256 registros. Caducar caché no borra el histórico persistente ni rejuvenece observaciones. |
| Ejecuciones transitorias de n8n | Configuración existente: poda a siete días y hasta 1.000 registros; sin guardar cuerpos de éxito/error. No afecta a recibos financieros de JAIME; no garantiza reducción física inmediata del SQLite. |
| Logs, capturas y resultados anteriores | Conservación, sin nueva purga automática. Crecimiento incluido en output. |

No se ha implementado limpieza destructiva ni movimiento automático. Si falta margen: revisar el inventario, comprobar el disco y ajustar justificadamente el presupuesto o diseñar una reubicación reversible. No borrar la base ni aumentar límites a ciegas.

## Pausa, recuperación e interfaz

Los workers comprueban el presupuesto antes de reclamar trabajo, llamar a la red o consumir cuota. Si falta margen, la cola permanece pendiente y no gasta intentos. Se reanuda al recuperar espacio. Los nuevos trabajos pueden responder 409 con STORAGE_*; los ciclos n8n conservan su plazo original y no se recrean ventanas vencidas. Las consultas de datos guardados y cancelaciones siguen disponibles. Un error de permisos de proveedor no se confunde con falta de disco.

Sistemas → Casos y entregas → Almacenamiento local. También desde Equipo → Supervisión del sistema. Muestra consumo, límites, libre en disco, fecha y conservación desplegable. GET `/api/storage/status` tiene contrato tipado. En desconexión se ocultan las cifras anteriores como estado actual.

## Verificación y límites

- `output/storage-final-check.log`: 525 backend, 111 frontend, una omisión preexistente; TypeScript y build correctos. Avisos preexistentes de TestClient y tamaño del bundle 3D.
- Pruebas sintéticas: límites, reserva, margen libre, inventario incompleto, referencias de runtime, exclusión concurrente, liberación del bloqueo, pausa/reanudación sin HTTP ni consumo de cuota, conservación de errores de permisos y órdenes prohibidas. No se llenó el disco real.
- `output/storage-preservation.json`: huellas y conteos iguales en 11 tablas protegidas, incluidos 18 modelos, ledger, cartera, listings, recibos y barras.
- `output/storage-browser.json` y `output/playwright/storage/`: panel real, escritorio/móvil, detalle plegado, bloqueo/recuperación simulados en navegador, desconexión y ausencia de errores JS. Capturas inspeccionadas.
- `output/storage-runtime.json`: estado READY real, órdenes 403, agenda original n8n 00/06/12/18 UTC intacta. Solo se recargó el backend.

Es un control de admisión de las rutas integradas, no una limitación de todo el ordenador. n8n, backups manuales, instalaciones y procesos externos pueden escribir independientemente; el margen libre se vuelve a medir. No se acredita funcionamiento continuo mientras el PC está apagado.

## Continuidad

Este requisito de almacenamiento de B2 queda entregado. Próximo: resolver divisa nativa e identidad temporal del piloto y diseñar una ampliación histórica acotada, revisando ajustes/acciones corporativas y derechos antes de descargar. Ningún dataset pasa a BACKTEST_READY por esta entrega. La investigación de IBKR es una propuesta de proveedor, no una conexión habilitada ni un cambio a ejecución.
