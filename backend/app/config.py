from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://dcim:dcim@localhost:5432/dcim"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    session_cookie_secure: bool = False  # Enable for any HTTPS deployment.
    session_hours: int = Field(default=8, ge=1, le=168)


settings = Settings()
