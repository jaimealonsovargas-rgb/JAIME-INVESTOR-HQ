# Pulido según referencia y resolución adaptativa · 2026-10-15

## Alcance y prioridad

La nueva referencia marcada y las correcciones del usuario en esta conversación prevalecen sobre el plano Sims anterior. Se conservan los nueve departamentos funcionales y los 16 NPC. Se omiten los departamentos de la imagen que no existen en el producto. Sistemas ocupa el despacho izquierdo y, conforme a la última imagen verde, **Ejecución queda justo debajo de Sistemas**, centrada en (-12, 3,6). Su anterior ubicación inferior derecha queda abierta. Comité y Recepción permanecen en el eje central; Trading y Performance, en el lateral derecho; Research, Quant y Riesgos, en la franja superior. No se añaden funciones de P3–P6.

La foto marcada fue aportada en la conversación. No se ha localizado un archivo original de esa imagen en el repositorio y no se le atribuye un hash inventado. Las referencias originales anteriores y su manifiesto siguen conservadas.

**Última corrección, antes de P3:** todos los despachos se adelantan **4,3 m**, conservando su distribución relativa; el frente de Recepción queda en z=11,0 y deja aproximadamente **2,7 m** hasta el borde arquitectónico. Se eliminan los muebles sueltos que ocupaban ese vestíbulo. Los seis laterales exteriores marcados pasan a ser paredes opacas y con colisión; los accesos interiores abiertos y los cristales decorativos interiores siguen siendo atravesables. El crema baja de `#c5b59b` a `#a7987e`. Fondo **`#000000`**, sin edificios, fotografía, niebla ni fachada inferior. Esta decisión sustituye la petición anterior de rascacielos.

## Cambios implementados

- Reutilización incremental de los builders, mobiliario, rigs y paneles existentes. Pasillos longitudinales de 3,3 m entre las salas centrales y laterales. Suelo de piedra azul negro y alfombras azul oscuro; se elimina el suelo marrón.
- Fondos crema oscuro, paños negros en Sistemas/Quant/Trading, zócalos y coronaciones negros y detalles de luz cálida. Laterales exteriores y perímetro opacos. Los doce grupos de vidrio interior y sus hojas con perfilería negra son decorativos y no generan colisión. Los muros y el mobiliario sí conservan colisiones.
- Carteles centrados sobre el fondo de cada sala, en plano vertical y con tamaño físico proporcionado. El texto sigue siendo DOM, independiente de la resolución del canvas. Marca JAIME INVESTOR preservada en mostrador y pared.
- Distribuciones diferenciadas: archivo y biblioteca, tres operadores en Trading, tres racks y dos puestos en Sistemas, mesa de comité transversal, pizarras con esquemas de proceso sin cifras financieras inventadas. 22 sillas: 15 ocupadas fuera del Comité y siete en el Comité, una ocupada.
- Tapetes de cuero, cantos metálicos y bandejas de cableado en mesas; cornisa y apliques en cada sala, armarios y accesorios de conferencia. Sombras PCF filtradas a 1024 en Equilibrado. Videowall **33×7,8 m**, frente a 32×4,8 m: **67,6 % más superficie**, nueve módulos de **1024×1536**, tipografía ampliada y marco fino. Se añade una vista de inspección Videowall. Los estados siguen procediendo del backend local; no se añaden gráficos de precios inventados.
- Cámara isométrica frontal, orientación fija y seguimiento suave. Flechas relativas a pantalla; velocidad de 2,05 m/s frente a 1,65 m/s. Minimap y teletransportes reflejan las nuevas posiciones. Videowall elevado para que no lo tapen los fondos de los despachos.
- El panorama urbano previo se conserva únicamente en `assets/retired` con licencia CC0 y hashes, fuera del runtime/build. Su carga, cilindro y materiales urbanos se han retirado. Oficina, mobiliario, personas y videowall siguen siendo geometría Three.js real.

## DPR adaptativo

Equilibrado automático empieza en **0,80**, con límites **0,70–1,00**. Se observan ventanas de dos segundos de marcha real. Bajo 44 FPS se requieren dos ventanas lentas; bajo 40 se permite reaccionar en la primera. La reducción es de 0,02, con al menos 2,5 s entre cambios. La recuperación es de 0,01 tras ocho segundos por encima de 54 FPS. Hay calentamiento y una gracia de 300 ms al cambiar de dirección.

Se excluyen reposo, pestaña oculta, panel abierto e inspección. El valor se sincroniza con la propiedad DPR de Canvas para evitar que una reconfiguración de React Three Fiber restablezca 0,80. Los cambios no afectan al tamaño CSS de paneles ni rótulos. El perfil **Equilibrado fijo (80 %)** permite una comparación reproducible. No se añaden dependencias ni servicios.

## Verificación funcional y seguridad

`python scripts/manage.py check`: **115 pytest + 40 Vitest y build correctos**. La primera comprobación detectó que el vidrio elevaba el número de mallas sobre el presupuesto; se fusionó con el departamento, sin retirar detalles. `python scripts/manage.py audit`: **0 vulnerabilidades conocidas** en Python/npm. Avisos: deprecación de TestClient/httpx y chunk principal 3D superior a 500 kB. Sin cambios en seguridad/backend P2.

Recorrido real por **9/9 departamentos** y apertura de sus **9/9 paneles**, caminando con flechas nativas, sin teletransportes ni escrituras de pose. Se guardan nueve textos de panel, rutas, posiciones y capturas. Las nueve zonas mantienen accesos y puntos de teletransporte libres en los tests de geometría. **16 NPC sentados / 17 rigs con el jugador**, 22 sillas y poses alineadas con sus mesas.

Verificados: cuatro direcciones de pantalla; WASD, ratón y rueda sin movimiento/orientación; no reapertura inmediata al cerrar; pausa y recuperación de control; Tab/Shift+Tab dentro del diálogo. Cristal interior de Recepción atravesable; muros laterales exteriores sólidos comprobados por segmento/collider. Backend inaccesible mediante abort de las peticiones locales del navegador: NO DISPONIBLE, sin cifras de sustitución y con movimiento operativo. `/?diagnostico=1` preservado.

**Regresión P2:** ningún módulo backend modificado. Peticiones HTTP locales reales con salud/schema `0002_data`, **98 instrumentos**, Data Quality y **nueve secciones HQ**; `POST /api/orders` devuelve **403 / P0_EXECUTION_DISABLED**. La lectura de las 15:01 UTC conserva **31 proveedores / 35 modalidades candidatas**, **33 adaptadores / 29 proveedores implementados**, **18 conexiones reales / 17 proveedores**, **11 fuentes utilizables / 11 proveedores**, **13 NO_CREDENTIALS** y **4 RIGHTS_RESTRICTED**. La frescura varía; no se suman mocks, consultas locales ni documentación como conexiones nuevas. No se han repetido consultas externas de todo el catálogo.

Los helpers de QA se ajustaron al vestíbulo nuevo: la prueba de las cuatro direcciones empieza alejándose del límite frontal y el recorrido conserva el destino exacto además de la rejilla de 25 cm. La espera de proximidad observa la apertura real hasta seis segundos en vez de presuponer un tiempo fijo. La captura detectó líneas por conflicto de profundidad en las pantallas lejanas; corregidas con sesgo de profundidad en el material, sin desplazar físicamente las pantallas ni añadir geometría. Código de cierre: **5d05209**.

## Rendimiento real

La tabla definitiva se obtiene de `comparacion-fijo-adaptativo.json` mediante `python scripts/qa_p1_corrective/summarize_dpr.py`. Chrome con ventana, Intel Graphics/D3D11, viewport **1920×1080**, Equilibrado con MSAA/sombras 1024, 16 NPC y videowall; ventanas nominales de 12 s con flechas nativas en Recepción, Trading, Comité y Sistemas. Pasadas fijo 0,80 → adaptativo → fijo 0,80 en el mismo build, sin compilaciones, suites de tests, auditorías ni refrescos externos simultáneos. Durante la recuperación hubo comandos ligeros de inspección/edición y una comprobación sintáctica JS; no se cerraron aplicaciones del usuario. Los arrays de fotogramas en movimiento permiten revisar medias, p95 y peor ventana móvil de cinco segundos. Se registra también el hash del bundle cargado.

| Zona | Fijo 0,80 antes | Adaptativo | DPR al final de la ventana | Fijo 0,80 después | Peor 5 s adaptativo |
|---|---:|---:|---:|---:|---:|
| Recepción | 59,84 | 58,37 | 0,99 | 59,82 | 56,10 |
| Trading | 57,78 | 57,70 | 1,00 | 56,16 | 54,56 |
| Comité | 58,12 | 60,00 | 1,00 | 59,48 | 59,77 |
| Sistemas | 56,13 | 59,83 | 1,00 | 57,81 | 59,58 |

Todas las cifras son **FPS en movimiento**. p95 adaptativo 17,2–21,7 ms. La recuperación realizó **20 cambios de +0,01 desde 0,80 hasta 1,00**. Al acabar el calentamiento estaba en 0,98 y continuó recuperando durante las mediciones. El margen permite hasta **56,25 % más píxeles** que el fijo 0,80; no se atribuye una mejora causal de FPS a diferencias pequeñas entre pasadas. En esta muestra se supera 40–45 en medias y ventanas móviles, sin prometer 45 en cada frame. No se necesitó bajar de 0,80: las bajadas hasta 0,70 están cubiertas por tests sintéticos, claramente separados de la medición Intel.

La deriva acumulada de las pulsaciones abrió Sistemas durante una muestra. Se conserva en `excludedSamples` (**5,03 s móviles**, excluida del resumen) y se repite completa; se reanudan las siete ventanas completas ya guardadas y la pasada fija restante. La corrección usa flechas reales para volver al eje, sin modificar la pose. El resultado final contiene **12 ventanas completas**. La comparación DOM se realiza a **DPR 1,00 frente a 0,80**: fuente 38 px, caja 320×46 idénticas. Panel abierto durante 5,2 s: DPR constante y personaje pausado.

**Limpieza posterior sin cambiar el modo de sombras renderizado:** la versión instalada Three 0.186.1 convertía PCFSoftShadowMap a PCFShadowMap en `WebGLShadowMap.js:99–102`. Se selecciona PCFShadowMap directamente para eliminar ese aviso. El A/B conserva los bundles medidos y una comprobación final separada (`smoke-pcf-final.json`) valida el build con el enum admitido. No se modifican la geometría, los mapas, la política DPR ni el filtro PCF. Las capturas finales corresponden a este build.

La comprobación final en Recepción da **59,74 FPS móviles**, p95 **17,8 ms**, DPR recuperando de 0,80 a **0,81**. Consola del build final: **cero errores**, aviso de THREE.Clock y un aviso X4122 de redondeo del compilador de shaders Intel/ANGLE; el programa compila y renderiza. No se parchea el controlador gráfico ni las dependencias.

Las capturas finales y los JSON funcionales están en [la carpeta de evidencia](evidencias/P1_PULIDO_ADAPTATIVO/README.md). Los primeros baselines de otra geometría y los intentos abortados no cuentan como prueba de FPS de esta versión; la primera comparación anterior a la corrección de profundidad se conserva en `historial/`.

## Limitaciones y siguiente paso

El resultado sigue siendo una oficina 3D interactiva optimizada para Intel; no se certifica equivalencia fotográfica exacta con la imagen conceptual. Los textos del videowall se inspeccionan con su vista dedicada o el centro de control DOM; desde la planta completa se ven a escala arquitectónica. Hay variación de rendimiento por batería, carga del equipo y navegador; una muestra satisfactoria no garantiza cada fotograma futuro. El perfil Detalle 1,35 no está certificado por esta comparación.

Noticias o precios caducados se mantienen marcados como tales; P3/P4/P5/P6 permanecen pendientes. Los NPC siguen siendo ambientación, sin actividad de IA ficticia. Las fuentes sin clave o con derechos restringidos conservan sus estados. Quedan los avisos de bundle >500 kB, deprecación de TestClient/httpx, THREE.Clock instanciado por R3F (dependencia, sin parchear node_modules) y redondeo X4122 del shader Intel. Siguiente paso: revisar visualmente esta entrega antes de iniciar P3 con su alcance correspondiente.

Coste de servicios adicional: **0 EUR**. PAPER ONLY. Detenerse antes de P3.
