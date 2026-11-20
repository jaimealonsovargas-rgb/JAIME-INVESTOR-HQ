# Consulta preparada para Alpaca — sin enviar

**Estado posterior:** el usuario ha aportado una respuesta de soporte a esta consulta. [Revisión y cierre B3.2 del 19-11](ENTREGA_B3_2.md). Se conserva el texto original preparado; el agente no envió el mensaje.

18-11-2026. Texto listo para el canal oficial [Contact → Support](https://alpaca.markets/contact). Enviar desde la cuenta correspondiente permitiría a Alpaca identificar las condiciones aplicables. No adjuntar claves, contraseñas, posiciones ni archivos `.env`.

**Asunto:** Personal IEX historical-data backtesting and private local retention

Hello Alpaca Support,

I have an Alpaca brokerage account as well as access to Paper trading. I am developing JAIME, a private application on my own Windows computer for personal, non-commercial investment research and simulated trading.

Before starting this experiment, could you confirm which terms apply to this specific use of the free IEX historical data available through my account?

- Retrieve daily, unadjusted OHLCV for Berkshire Hathaway Class B (BRK.B): the last 252 official trading sessions ending on 31 December 2025, with relevant calendar and corporate-action metadata.
- Keep the responses and normalized bars privately on my local computer, including SQLite and any local backup copies, for at most 30 days after retrieval. This would support repeatable automated Python backtests and checks without repeatedly downloading the same observations.
- Calculate moving averages and simulated performance locally; retain private experiment parameters, hashes and aggregate performance metrics. No prices, extracts or datasets would be redistributed, published, sold, uploaded to cloud backups, or sent to external AI services.
- Use this experiment only for my own research. No live trading or third-party service is involved, and I do not want a paid data plan or billable entitlement activated.

Your Historical API documentation describes backtesting as an intended use, and the Terms and Conditions describe personal, non-commercial use. Section 30 of the public Customer Agreement V26.2026.07 also restricts reproduction of market data without written consent. Does the private copying and reuse described above fall within the existing permission for my account, or is additional consent required?

Please identify any applicable account/subscriber classification, additional IEX or other provider terms, retention/deletion requirements (including backup copies), and whether hashes and aggregate backtest metrics may be kept after the source data is removed. A link to existing applicable terms that expressly cover this use would also be helpful. If this use requires a fee, please say so without activating any paid service.

Thank you.

---

La respuesta debe cubrir el uso concreto; una confirmación genérica de acceso a la API no demuestra retención o reutilización autorizadas. Los 30 días son una propuesta de alcance, no un derecho ya concedido. Este archivo no ha creado un correo ni enviado información a Alpaca.
