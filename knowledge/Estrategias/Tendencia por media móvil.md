---
tipo: estrategia
revisado: 2026-11-25
---

# Tendencia por media móvil

La familia `SMA_LONG_CASH` compara el último cierre disponible con la media de los últimos cierres. Un cierre estrictamente superior activa exposición larga en la apertura siguiente. Con igualdad o por debajo, el objetivo es efectivo. El protocolo usa la apertura IEX como aproximación y aplica costes.

| Variante registrada | Ventana | Resultado de B4 |
| --- | ---: | --- |
| `sma20` | 20 cierres | Descartada |
| `sma40` | 40 cierres | Descartada |
| `sma60` | 60 cierres | Descartada |

La [[Campaña retrospectiva B3.2]] fijó 60 sesiones de calentamiento común. Cada configuración se contrastó frente a [[Efectivo]] y [[Comprar y mantener]] bajo costes base y adversos. El criterio requería superar ambos controles en rentabilidad neta y limitar la caída máxima. [[Selección de estrategias B4]] conserva los descartes. [Protocolo congelado](https://github.com/jaimealonsovargas-rgb/JAIME-INVESTOR-HQ/blob/bf4a5b9d61071a94228f529876eb33d1bf18d3db/docs/actual/B3_2_PROTOCOLO_v1.json) · [Informe B4](https://github.com/jaimealonsovargas-rgb/JAIME-INVESTOR-HQ/blob/bf4a5b9d61071a94228f529876eb33d1bf18d3db/docs/actual/ENTREGA_B4.md)
