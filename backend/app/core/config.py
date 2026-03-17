from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Modular Monolith Banking API"
    database_url: str = "postgresql+psycopg2://postgres:postgres@db:5432/banking"
    jwt_secret: str = "change-me-for-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_allowed_origins: str = "http://localhost:8080,http://127.0.0.1:8080"
    rate_limit_requests: int = 50
    rate_limit_window_seconds: int = 60
    log_level: str = "INFO"
    websocket_poll_seconds: int = 2

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origins_list(self) -> list[str]:
        if self.cors_allowed_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


settings = Settings()
