from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "dev"
    secret_key: str = "dev-only-change-me"
    database_url: str = "sqlite:///./dev.db"
    access_token_minutes: int = 30
    refresh_token_days: int = 30
    cors_origins: str = "http://localhost:5173,http://localhost:8000"

    superadmin_phone: str = ""
    superadmin_password: str = ""
    superadmin_name: str = "Platform Owner"

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()

if settings.app_env == "prod" and settings.secret_key == "dev-only-change-me":
    raise RuntimeError("Production'da SECRET_KEY o'zgartirilishi shart")
