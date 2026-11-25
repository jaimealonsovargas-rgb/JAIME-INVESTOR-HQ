---
tipo: integración
revisado: 2026-11-25
---

# Simulador local B6.1

El simulador transforma un recibo admisible de [[Decisión de riesgo B5]] en una intención con identificador estable. Reserva efectivo o acciones en la cuenta ficticia. El estado que conoce JAIME y el que conoce el bróker ficticio se guardan por separado.

Cuando se pierde una respuesta, `UNKNOWN` conserva la reserva hasta aclarar el estado. Cada ejecución tiene una identidad propia. En un ensayo publicado, una compra ficticia de diez acciones se canceló después de ejecutar cuatro. Al reabrir la base, el total siguió en cuatro.

[[Cola de envíos B6.2]] amplía la recuperación entre procesos. [[B6.3 Conciliación del simulador]] extiende la comprobación al conjunto de ejecuciones y posiciones de la cuenta. [Contrato y escenarios de prueba](https://github.com/jaimealonsovargas-rgb/JAIME-INVESTOR-HQ/blob/bf4a5b9d61071a94228f529876eb33d1bf18d3db/docs/actual/ENTREGA_B6_1.md)
