from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # ── Database ──
    DATABASE_URL: str = "postgresql+asyncpg://uniconnect:uniconnect_dev_pwd@db:5432/uniconnect"
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: float = 30.0
    DB_POOL_RECYCLE: int = 1800
    DB_POOL_PRE_PING: bool = True

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
    # Comma-separated list of trusted proxy IPs/networks for X-Forwarded-For parsing.
    # Only proxies listed here are trusted to set forwarded headers.
    # Default "127.0.0.1" trusts only loopback; set to actual proxy IPs in production.
    TRUSTED_PROXY_IPS: str = "127.0.0.1"

    @property
    def trusted_proxy_list(self) -> list[str]:
        return [ip.strip() for ip in self.TRUSTED_PROXY_IPS.split(",") if ip.strip()]

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
    GEMINI_PRIMARY_MODEL: str = "gemini-2.5-flash"
    GEMINI_FALLBACK_MODELS: str = "gemini-2.0-flash,gemini-1.5-flash"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    model_config = {"env_file": (".env", "../.env"), "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
