"""Secretos opcionales: solo backend; no se exponen mediante contratos públicos."""
from pydantic import ConfigDict, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from app.config import ROOT

class DataSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / '.env', extra='ignore', hide_input_in_errors=True)
    data_public_enabled: bool = True
    data_auto_refresh_enabled: bool = True
    data_disabled_sources: str = ''
    agent_reach_public_enabled: bool = False
    vibe_data_adapter_enabled: bool = False
    liquid_public_readonly_enabled: bool = False
    sec_contact: SecretStr | None = None
    fred_api_key: SecretStr | None = None
    bea_api_key: SecretStr | None = None
    bls_api_key: SecretStr | None = None
    eia_api_key: SecretStr | None = None
    alpha_vantage_api_key: SecretStr | None = None
    coingecko_demo_api_key: SecretStr | None = None
    openfigi_api_key: SecretStr | None = None
    alpaca_api_key: SecretStr | None = None
    alpaca_secret_key: SecretStr | None = None
    trading212_api_key: SecretStr | None = None
    trading212_api_secret: SecretStr | None = None
    twelve_data_api_key: SecretStr | None = None
    fmp_api_key: SecretStr | None = None
    massive_api_key: SecretStr | None = None
    tiingo_api_key: SecretStr | None = None

    def secret(self, field: str) -> str | None:
        value = getattr(self, field, None)
        return value.get_secret_value().strip() or None if value else None
