> ARCHIVO INACTIVO · copia anterior a la auditoría del 11-11-2026. Sus próximos pasos y autorizaciones no gobiernan el trabajo actual. Enlaces relativos reubicados; contenido histórico conservado.

# IBKR — requisitos del piloto de lectura

Actualizado 11-11-2026, Europe/Madrid. **Piloto real de lectura y conciliación de contratos completados**: sesión Paper, reloj y tres contratos, con revisión posterior SEC/Alpaca y USD documentado para la observación. SDK oficial aislado, API local de solo lectura. [Resultado, controles y operación](../../../../../integrations/ibkr/README.md) · [Entrega de la conciliación](../../../../actual/ENTREGA_B2_3_CONTRATOS_IBKR.md). Siguiente: identidad histórica; precios/históricos IBKR y sus derechos siguen pendientes. Las secciones siguientes conservan el plan inicial del 09-11.

## Comprobado inicialmente el 09-11 (histórico, superado por el piloto del 11-11)

El usuario indica que aún no tiene cuenta y puede crearla. Entorno local Python 3.14.4; `ibapi` y `protobuf` no instalados en el entorno del proyecto. Sin carpetas TWS/Gateway en las rutas estándar comprobadas; no demuestra ausencia en rutas personalizadas. No se han importado SDKs, abierto sockets del broker, leído credenciales ni consultado cuentas.

Nuevo diagnóstico reproducible `scripts/ibkr_preflight.py`: estado NOT_READY, razones independientes y declaración de cuenta separada de verificación real. Un directorio o paquete presente nunca produce CONNECTED. Informe privado: `output/ibkr-preflight-20261109.json`. Exportación bajo el presupuesto de almacenamiento, sin sobrescribir informes.

```powershell
.venv/Scripts/python.exe scripts/ibkr_preflight.py
```

Cuando el usuario declare acceso Paper se puede repetir con `--account-state paper_declared`; esa opción no acredita autenticación ni permisos. Usar un nuevo nombre para `--output`. El script ha sido ejecutado en el entorno real: cero peticiones de red, sin cambios de dependencias o datos financieros. No es un test de integración IBKR ni se repitió la suite de la entrega anterior.

## Cuenta de prueba y Paper no son equivalentes

La [FAQ oficial de integraciones](https://www.interactivebrokers.com/docs/third-party-integrations/general-third-party-frequently-asked-questions) permite conexión TWS API con trial, pero indica que no ofrece tiempo real ni velas históricas para la mayoría de instrumentos. En cambio, una [respuesta de soporte en IBKR Campus](https://www.interactivebrokers.com/campus/trading-lessons/request-paper-trading-account/) indica que las cuentas trial no están soportadas por las APIs. No resolver esa discrepancia prometiendo acceso gratuito: confirmar la elegibilidad concreta con IBKR y verificar lo recibido. Una demostración visual no acredita acceso a datos API.

El usuario puede iniciar la solicitud en el [portal oficial de cuentas](https://interactivebrokers.ie/en/accounts/individual.php), utilizando sus datos reales y su país de residencia. El tipo de cuenta debe responder a sus necesidades y elegibilidad, no a un atajo del proyecto. La apertura, documentación personal y MFA corresponden al usuario. No se solicitan contraseñas en el chat ni se automatiza esa solicitud.

Si IBKR exige financiación o una suscripción para activar la funcionalidad buscada, ese requisito no queda autorizado por esta tarea; registrar la limitación y continuar B2 con las fuentes existentes. La documentación de [Paper](https://www.interactivebrokers.com/docs/tws-api/doc/notes-limitations/tws-api-limitations) describe requisitos de cuenta regular aprobada/financiada; no se afirma que una solicitud sin fondos ya habilite el piloto.

## Próxima sesión técnica

1. Confirmar qué acceso obtiene el usuario: solicitud pendiente, trial o Paper habilitado; sin recopilar identificadores privados innecesarios.
2. Preparar SDK oficial revisado/pinado y comprobar compatibilidad real con Python 3.14 antes de tocar dependencias del backend. No instalar un `ibapi` de procedencia/versión no comprobada ni ejecutar el Testbed de órdenes.
3. TWS o IB Gateway en sesión Paper, API local y Read-Only activado; verificar el entorno por configuración/cuenta, no solo por el puerto. Los valores por defecto son 7497 (TWS Paper) y 4002 (Gateway Paper), pero son configurables. [Conexión oficial](https://www.interactivebrokers.com/docs/tws-api/sync-doc/connect-start-connection).
4. Adaptador con métodos de lectura permitidos para resolver contratos. No activar precios/históricos sin comprobar derechos, coste y tipo de feed recibido. Órdenes siempre 403.
5. Resolver Apple/Microsoft/Walmart y contrastar moneda/plaza/clase con evidencia fechada; discrepancias y ambigüedades bloquean la unión. Después, una acción europea y un histórico acotado sujeto a presupuesto.

No se declara cerrado el piloto de datos ni resuelta la divisa de las tres acciones. La siguiente dependencia externa es el acceso del usuario; el siguiente desarrollo técnico es el adaptador de contratos y su prueba de compatibilidad. Almacenamiento entregado, 18 modelos conservados y P4 PARTIAL sin cambios.
