from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

_BASE_DIR = Path(__file__).resolve().parent.parent
_ENV_FILE = _BASE_DIR / ".env"
if not _ENV_FILE.exists():
    _ENV_FILE = _BASE_DIR.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: SecretStr
    openai_model: str = "gpt-4o"

    google_client_id: str = ""
    google_client_secret: SecretStr = SecretStr("")
    jwt_secret: SecretStr = SecretStr("change-me-in-production")

    database_url: str = f"sqlite+aiosqlite:///{_BASE_DIR / 'data' / 'app.db'}"
    frontend_url: str = "http://localhost:3000"

    log_level: str = "INFO"


settings = Settings()  # type: ignore[call-arg]
