---
tipo: documentación
revisado: 2026-11-25
---

# Almacenamiento y procedencia

SQLite en modo WAL conserva los hechos y los registros del proyecto. En la entrega consultada el esquema es `0015_history_batches`. MASTER, los ensayos cuantitativos y la cuenta del simulador tienen dominios contables separados.

- **Fuentes.** [[SEC y EDGAR]] aporta documentos y cuentas. [[Alpaca]] aporta el histórico acotado de BRK.B/IEX. [[IBKR]] complementa la identidad de contratos. Cada uso depende de la fuente, el instrumento, el periodo y los derechos revisados.
- **Investigación.** Los originales y recibos privados viven en `data/` y `output/`. Las fichas guardan identificadores, fechas, conclusiones y referencias a las entregas. La admisión D3 verifica identidad, calendario, acciones corporativas y disponibilidad temporal según el protocolo.
- **Simulación.** [[Simulador local B6.1]] guarda su propio diario. El expediente de [[Selección de estrategias B4]] se puede contrastar con su huella de contenido.

[Almacenamiento](https://github.com/jaimealonsovargas-rgb/JAIME-INVESTOR-HQ/blob/bf4a5b9d61071a94228f529876eb33d1bf18d3db/docs/actual/ENTREGA_B2_ALMACENAMIENTO.md) · [Admisión D3](https://github.com/jaimealonsovargas-rgb/JAIME-INVESTOR-HQ/blob/bf4a5b9d61071a94228f529876eb33d1bf18d3db/docs/actual/ENTREGA_D3_ADMISION.md) · [Estado y esquema](https://github.com/jaimealonsovargas-rgb/JAIME-INVESTOR-HQ/blob/main/STATUS.md)
