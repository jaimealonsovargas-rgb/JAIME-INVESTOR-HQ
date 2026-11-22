# B6 · Contrato de órdenes y simulador local

22 de noviembre de 2026, Europe/Madrid. JAIME puede convertir una decisión de riesgo admisible en una intención de orden y seguirla aunque se pierda la respuesta del bróker ficticio. La primera comprobación sobre un ciclo real dio **cero intenciones para BRK.B**.

## Ciclo real comprobado

| Evidencia del domingo 22 | Resultado |
|---|---|
| Activación de n8n | 19:00 Madrid, ejecución `n8n:10` |
| Ciclo SEC | `9dbd2b231294c69c55a6fc4e4012aee83e80452c5e4abcb510eb51ae812d8b46` |
| Recibo B5, política PAPER v2 | `421fd98d362021821e5be5aaf9184ebc3f3e68c116eed95fb9f180bd3ecedcc9` |
| Validación de BRK.B | `NO_CANDIDATES`, tres hipótesis descartadas por B4 |
| Consumo por B6 | Cero intenciones y cero envíos. Repetir la consulta devolvió el mismo resultado. |

n8n inicia la investigación y B5 persiste el recibo. En este hito, el comando de B6 abre la base de JAIME en modo de solo lectura. Una observación o un veto termina la comprobación antes de abrir la base del simulador. [Riesgo B5](ENTREGA_B5.md) · [Validación B4](ENTREGA_B4.md).

## Cómo reproducirlo

Desde la raíz del repositorio en PowerShell, el primer comando inspecciona el último ciclo registrado. Se puede sustituir `latest` por el ID del ciclo del domingo. El segundo utiliza exclusivamente la cuenta y las cotizaciones ficticias incluidas en el proyecto.

```powershell
.\.venv\Scripts\python.exe scripts/probe_paper_simulator.py --cycle latest
.\.venv\Scripts\python.exe scripts/probe_paper_simulator.py --demo
```

## Qué comprueba el contrato

- Una compra o venta requiere que coincidan el ciclo, la huella del recibo, la política de riesgo, el expediente y el paquete revisado de cuenta, precios y comité. El simulador reproduce B5 y comprueba la vigencia al admitir la intención y al enviarla. Una segunda decisión que reutiliza la misma aprobación encuentra la intención anterior.
- Cada intención identifica decisión, cuenta, instrumento, lado y cantidad. Conserva también el precio límite, la divisa, las referencias de cotización y liquidez, el vencimiento y el identificador del comité. La compra usa el precio vendedor como límite y reserva efectivo con el margen de coste de B5. La venta usa el precio comprador y reserva acciones. Los importes usan aritmética decimal.
- El estado que conoce JAIME y el estado que conoce el bróker ficticio se guardan por separado. Una respuesta perdida lleva a `UNKNOWN`. La reserva persiste incluso después del vencimiento local mientras el resultado sea incierto. Para reenviar se exige una confirmación de ausencia del bróker ficticio y una intención todavía vigente. Una consulta sin visibilidad conserva la incertidumbre.
- Cada intento y cada ejecución llevan un ID. Repetir el mismo evento devuelve su recibo original. Reutilizar su ID para otro importe u otra orden produce un conflicto. Una notificación tardía no puede reabrir una cancelación ni sumar dos veces una ejecución. La consulta de la orden devuelve el estado actual.
- Cada laboratorio comparte una única cuenta, posiciones y cotizaciones revisadas. Conserva hasta 512 intenciones en SQLite. La demostración usa carpetas temporales independientes. La inspección de un ciclo positivo reserva espacio mediante el control local de almacenamiento y guarda su diario bajo `output/paper-simulator/reviewed`. El esquema y la contabilidad de MASTER siguen separados.

El identificador estable y la consulta por él preparan la futura integración con Alpaca. La confirmación inequívoca de ausencia es una propiedad del simulador. El futuro conector deberá acreditar cómo resuelve estados inciertos con respuestas reales. [Documentación oficial de órdenes de Alpaca](https://docs.alpaca.markets/us/docs/orders-at-alpaca).

## Resultados de la cuenta ficticia

Cada escenario comenzó con la misma intención de comprar diez acciones ficticias. Se repitió cada evento después de reabrir la base. Los siete resultados tienen la huella `f03da0432be1069ff90651ff2026bcaa1b3f9703bf6e859a50b3fd0088418168`.

| Escenario | Estado final | Acciones ejecutadas |
|---|---|---:|
| Aceptación y ejecución completa | Ejecutada | 10 |
| Rechazo explícito | Rechazada | 0 |
| Respuesta perdida tras aceptar, consulta y cancelación | Cancelada | 0 |
| Pérdida antes de recibir el envío, ausencia confirmada y reintento | Aceptada | 0 |
| Ejecución parcial y respuesta perdida al cancelar | Cancelada | 4 |
| Ejecución completa antes de la cancelación y aviso tardío | Ejecutada | 10 |
| Fin de sesión después de una ejecución parcial | Caducada | 3 |

Pasaron las **887 pruebas del backend**, incluidas **34 del simulador**, y las **115 de la interfaz**. La compilación de producción terminó correctamente. Las pruebas cubren dos decisiones que compiten por el mismo presupuesto, ocho repeticiones concurrentes de una ejecución, un cambio de política de riesgo y la reapertura desde otro proceso.

Las huellas de las cuatro tablas de MASTER coincidieron antes y después de la comprobación real. El esquema de JAIME sigue en `0015_history_batches`. La web, la API y n8n respondieron en localhost y la ruta pública de órdenes devolvió HTTP 403.

**Siguiente entrega.** Guardar atómicamente la intención, la reserva y el envío pendiente, y recuperar ese trabajo tras una caída frente al mismo simulador. La conciliación de posiciones y la conexión externa a Alpaca PAPER tienen sus propios hitos. [Ficha activa](../../tasks/ACTUAL.md) · [Hoja de ruta](../../tasks/ROADMAP.md).
