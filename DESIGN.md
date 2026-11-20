---
name: JAIME Investor HQ
description: Sede financiera 3D antracita con luz amarilla arquitectónica y paneles de inversión discretos.
colors:
  led-core: "#fff82e"
  accent-yellow: "#e5ff00"
  warm-wash: "#ffcd83"
  anthracite-wall: "#25282c"
  charcoal-structure: "#14171a"
  floor-tint: "#171a1d"
  reception-stone-tint: "#424548"
  walnut-tint: "#b28f69"
  bronze: "#b9915e"
  rail-surface: "#111517"
  dialog-surface: "#14191c"
  control-surface: "#181e20ee"
  control-hover: "#313938"
  rail-border: "#393d3f"
  text: "#edf0ed"
  title-text: "#f1f1ec"
  muted-text: "#aeb7b5"
  available: "#a7d7be"
  stale-estimated: "#d9c693"
  missing: "#b5bebc"
typography:
  body:
    fontFamily: 'Arial, "Segoe UI", sans-serif'
    fontSize: "14px"
    lineHeight: 1.5
  title:
    fontFamily: "Arial, sans-serif"
    fontSize: "16px"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "0"
  dialog-title:
    fontFamily: "Arial, sans-serif"
    fontSize: "30px"
    lineHeight: 1.2
    letterSpacing: "-.015em"
  metric:
    fontFamily: 'Arial, "Segoe UI", sans-serif'
    fontSize: "30px"
    fontWeight: 500
    lineHeight: 1.2
    letterSpacing: "-.035em"
  detail:
    fontFamily: 'Arial, "Segoe UI", sans-serif'
    fontSize: "12px"
    lineHeight: 1.6
rounded:
  control: "5px"
  monitor-control: "3px"
  portfolio: "8px"
  rail: "10px"
  dialog: "12px"
spacing:
  compact: "8px"
  row: "12px"
  section: "16px"
  rail: "18px"
  roomy: "24px"
  dialog-inline: "30px"
components:
  office-button:
    backgroundColor: "{colors.control-surface}"
    textColor: "#e8dfd1"
    rounded: "{rounded.control}"
    padding: "10px 16px"
  office-button-hover:
    backgroundColor: "{colors.control-hover}"
  view-active:
    backgroundColor: "{colors.accent-yellow}"
    textColor: "#171c1c"
    rounded: "{rounded.control}"
    padding: "10px 16px"
  rail:
    backgroundColor: "{colors.rail-surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.rail}"
    width: "304px"
  rail-select:
    backgroundColor: "#1b2022"
    textColor: "#e2e6e0"
    rounded: "{rounded.control}"
    padding: "6px"
  monitor-dialog:
    backgroundColor: "{colors.dialog-surface}"
    textColor: "#ece8df"
    rounded: "{rounded.dialog}"
    width: "min(1120px, calc(100vw - 64px))"
---

# Design System: JAIME Investor HQ

## Overview

**Creative North Star: "Sede financiera oscura y legible"**

La entrada es una oficina 3D real, antracita, con nogal, piedra carbón y luz amarilla incorporada a la arquitectura. El espacio permanece visible entre controles discretos. La recepción combina un mostrador central, frente oscuro, extremos estriados, pared de piedra y listones de nogal; el rótulo JAIME queda integrado en esa pared.

Los paneles presentan primero lo esencial. Procedencia, explicaciones y diagnóstico se consultan al desplegar, sin ocultar estados de ausencia o antigüedad. Esta documentación recoge la sede y sus paneles actuales; no convierte los estilos de otras superficies de la aplicación en una nueva identidad.

**Key Characteristics:**

- Arquitectura antracita con LED amarillo saturado y luz cálida local.
- Nogal, piedra, metal y vidrio como materiales 3D, sin imagen sustitutiva del espacio.
- Datos principales legibles y detalle voluntario mediante controles nativos.
- Nueve departamentos, dieciséis personajes y navegación espacial conservados.

## Colors

El amarillo LED (`led-core`) forma el núcleo físico; `accent-yellow` colorea halo, selección y foco. `warm-wash` acompaña la arquitectura con luz cálida local. Nogal y bronce dan calidez al mobiliario; antracita, carbón y piedra sostienen el espacio. Los tintes de madera, suelo y piedra se combinan con texturas y shaders: no representan el color final de un píxel.

Los paneles usan superficies oscuras, bordes finos y texto claro. Los colores de disponibilidad, antigüedad y ausencia acompañan etiquetas explícitas.

**The Local Light Rule.** El halo pertenece a una superficie arquitectónica; no aplicar bloom a toda la pantalla.

## Typography

Se conservan Arial y las fuentes instaladas del sistema. Los laterales usan Arial con Segoe UI como alternativa; los diálogos usan Arial y la base conserva system-ui. No se añade una familia externa. La jerarquía del frontmatter recoge cuerpo, títulos, valor principal y detalle; las métricas usan números tabulares. Los textos de marca existentes se mantienen sin convertir las etiquetas espaciadas en una norma para nuevos paneles.

## Layout

Escena a pantalla completa, planta de 34 × 28 m y nueve departamentos. Riesgos está en x = 12, alineado con Trading y Performance. Recepción de 6,3 m; puestos de 2,3 m o 2,85 m según configuración. Asientos, accesos y colisiones siguen esa geometría. Se conservan cámara, vistas y movimiento relativo a pantalla.

Laterales de 304 px, o 328 px en densidad normal; relleno de 18 px o 22 px. Bajo 1280 px pasan a 280 px. A 760 px o menos, ambos encabezados permanecen accesibles y solo se abre un contenido a la vez, con márgenes de 12 px. Los controles inferiores se distribuyen en filas. Las fichas pasan a una columna a 700 px.

## Elevation & Depth

La profundidad procede de geometría, materiales, vidrio, sombras de contacto e iluminación. Las cuatro luces puntuales añadidas en recepción y extremos de pasillo no proyectan sombras; los halos usan shaders locales. Se conserva la iluminación previa, incluida la direccional con sombras. Sin postprocesado de bloom ni nuevas dependencias.

Bordes y capas oscuras separan la interfaz; los laterales tienen sombra contenida y los diálogos una más amplia con fondo modal. El sidecar conserva sombras y transiciones exactas. Los botones responden a hover y pulsación; sus transiciones se desactivan con movimiento reducido.

## Shapes

Arquitectura rectilínea y cantos de mobiliario suavizados. Controles pequeños, laterales de 10 px de radio y diálogos de 12 px. Pestañas planas con línea amarilla al seleccionarse. Filas y divisores organizan datos sin envolver cada valor en una tarjeta.

## Components

- **Controles:** fondo oscuro, borde fino, hover más claro y foco amarillo de 2 px; vista activa amarilla con texto oscuro. Selectores nativos y teclado conservados.
- **Laterales financieros:** encabezado estable, contenido desplazable y densidad seleccionable. Patrimonio, caja, P&L y posiciones primero; referencias y diagnóstico plegados.
- **Mercado:** símbolo, precio, cambio, estado y procedencia legibles; detalle y serie al desplegar cuando existen.
- **Personas:** mandato, trabajo y entrega como contenido principal; capacidades, explicación y diagnóstico bajo demanda.
- **Diálogos y videowall:** cifras tabulares, fuentes desplegables, cierre con Escape y gestión del foco. El regreso conserva la oficina como contexto.

## Do's and Don'ts

### Do:

- **Do** conservar la entrada 3D, nueve departamentos, dieciséis personajes y controles de navegación.
- **Do** mantener el amarillo saturado en LED, selección y foco, con iluminación cálida localizada.
- **Do** mostrar ausencia, antigüedad, fuente y fecha según los datos disponibles.
- **Do** presentar datos principales antes del detalle desplegable y mantener acceso por teclado.
- **Do** reutilizar geometrías y materiales, con asientos y colisiones coherentes con el mobiliario.

### Don'ts:

- **Don't** sustituir la oficina por un fondo raster ni añadir bloom de pantalla completa.
- **Don't** convertir el suelo en azul ni blanquear el núcleo amarillo de los LED.
- **Don't** inventar cifras, gráficas, actividad, ejecución o frescura para completar un diseño.
- **Don't** tratar las dimensiones anteriores del mobiliario o la antigua posición de Riesgos como restricciones vigentes.
- **Don't** presentar esta documentación como equivalencia fotográfica, medición de FPS o aceptación financiera.
