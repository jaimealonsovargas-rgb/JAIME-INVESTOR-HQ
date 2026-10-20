# Actualización P2 real — 20 octubre 2026

`migration-real.json`: backup previo, migración `0005_data_history`, Alembic sin drift y hash MASTER conservado.

`sources-real.json`: pasada real del catálogo mediante cliente HTTP seguro y prueba del scheduler persistente. 35 modalidades; 17 conexiones verificadas en esta pasada (16 HTTP nuevas y una caché verificada); 12 utilizables bajo derechos P2; 2 brókeres excluidos. Los contadores de `quality` son acumulados históricos, no conexiones nuevas. No confundir uso P2 con permiso para valoración o IA.

`eurostat-ecoicop2-real.json`: verificación posterior a esa pasada; reemplaza el preset archivado por ECOICOP2/base 2025. Es la misma modalidad A04, no otro proveedor. Contiene los tres datos reales recibidos y su atribución.

El archivo de 730 observaciones de la pasada inicial permanece en SQLite local; la corrección Eurostat añade su nueva serie sin fusionar unidades. Backup y base no se publican. No se incluyen secretos. Esta evidencia valida el tramo de datos, **no cierra el E2E generativo P4**.
