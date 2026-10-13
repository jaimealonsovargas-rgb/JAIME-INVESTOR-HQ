from types import MappingProxyType


class PaperOnlyViolation(ValueError):
    pass


class ExecutionUnavailable(RuntimeError):
    pass


# Coincidencia exacta: excluye userinfo, puertos, query, fragmentos y subdominios.
PAPER_BASE_URLS = MappingProxyType({
    "ALPACA_PAPER": "https://paper-api.alpaca.markets",
    "T212_DEMO": "https://demo.trading212.com/api/v0",
})


def validate_paper_endpoint(provider: str, base_url: str) -> str:
    if provider not in PAPER_BASE_URLS or base_url != PAPER_BASE_URLS[provider]:
        raise PaperOnlyViolation("Destino rechazado: solo se permiten bases PAPER/DEMO exactas.")
    return base_url


def deny_order_execution() -> None:
    # Incondicional: ningún toggle, credencial, chat o LLM puede habilitar órdenes en P0.
    raise ExecutionUnavailable("NO DISPONIBLE: ejecución de órdenes bloqueada en P0.")
