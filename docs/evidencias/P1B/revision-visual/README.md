# Revisión de acabado de P1.B · 14-10-2026

Capturas reales del build final, Chrome/WebGL con ANGLE Intel Graphics D3D11, 1920×1080 y perfil Equilibrado:

- [Recepción](01-recepcion.png): 56,2 FPS.
- [Planta completa](02-planta.png): 53,7 FPS.
- [Trading Floor](03-trading.png): 59,2 FPS.
- [Comité](04-comite.png): 59,3 FPS.

Los cuatro `*-equilibrado.json` registran benchmarks de 12 s en una sesión headless aislada, con hasta 600 intervalos, foco/visibilidad, pose y resolución comprobados. Alimentación de red detectada durante las medidas finales. No son FPS de reposo ni una garantía para cualquier estado del equipo.

`referencia-anterior-AC-headless.json`: build anterior en la misma sesión aislada (57,78 FPS en recepción; cámara anterior). `referencia-anterior-misma-sesion.json`: referencia anterior con batería baja (29,72 FPS). `ensayo-luces-area-descartado.json`: variante experimental retirada, **no representa el código entregado**.

Pruebas, contexto energético, pérdidas y límites en [STATUS.md](../../../../STATUS.md). Arquitectura general aprobada; acabado pendiente de aprobación. No implementa P1.C–F.
