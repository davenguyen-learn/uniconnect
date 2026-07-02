from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # ── Database ──
    DATABASE_URL: str = "postgresql+asyncpg://uniconnect:uniconnect_dev_pwd@db:5432/uniconnect"
    DB_ECHO: bool = False

    # ── JWT ──
    JWT_SECRET: str = "change-me-to-a-random-64-char-string-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 60

    # ── App ──
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # ── Server ──
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000

    # ── Storage (Cloudflare R2) ──
    R2_ENDPOINT_URL: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = "uniconnect"
    R2_PUBLIC_URL: str = ""
    MAX_FILE_SIZE: int = 10_485_760  # 10MB
    ALLOWED_FILE_TYPES: str = "application/pdf,image/jpeg,image/png,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    # ── AI Services ──
    GEMINI_API_KEY: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
