import os
from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARENT_DIR = os.path.dirname(BASE_DIR)

# Authoritative canonical SQLite database (02backend/app/yojnasetu.db)
DEFAULT_DB_FILE = os.path.join(BASE_DIR, "yojnasetu.db")



class Settings(BaseSettings):
    PROJECT_NAME: str = "YojnaSetu API"
    API_V1_STR: str = "/api/v1"
    ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # CORS configuration
    BACKEND_CORS_ORIGINS: List[str] = [
        "https://yojnasetu-arthnex.vercel.app",
        "https://01frontend-nine.vercel.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Security configuration
    SECRET_KEY: str = "yojnasetu_dev_secret_key_change_in_production_9f8a7b6c5d4e3f2a1b"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Database configuration
    POSTGRES_SERVER: Optional[str] = None
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    DATABASE_URL: Optional[str] = None

    # Database connection pool settings (for PostgreSQL / Production)
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    DB_ECHO: bool = False
    SQLITE_ENABLE_FOREIGN_KEYS: bool = False

    # AI Provider configuration
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-flash-latest"
    OPENAI_API_KEY: Optional[str] = None
    AI_PROVIDER: str = "auto"  # auto, gemini, openai, dev_fallback

    # Google Authentication configuration
    GOOGLE_CLIENT_ID: Optional[str] = None

    # Government Scheme Ingestion & Auto-Scheduler configuration (24-hour cadence)
    MYSCHEME_API_KEY: Optional[str] = None
    SCHEME_INGESTION_ENABLED: bool = True
    SCHEME_INGEST_INTERVAL_HOURS: int = 24
    SCHEME_INGEST_INTERVAL_DAYS: int = 1
    SCHEME_INGESTION_INTERVAL_MINUTES: int = 1440
    SCHEME_INGESTION_BATCH_SIZE: int = 50
    SCHEME_INGESTION_REQUEST_TIMEOUT_SECONDS: int = 15
    SCHEME_INGESTION_RETRY_BACKOFF_HOURS: int = 2

    # Email configuration
    EMAIL_PROVIDER: str = "none"  # none, smtp, console
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    EMAIL_FROM: str = "noreply@yojnasetu.gov.in"
    YOJNASETU_BASE_URL: str = "http://localhost:3000"

    @field_validator("DEBUG", mode="before")
    @classmethod
    def normalize_debug_value(cls, value):
        """Accept legacy deployment labels such as DEBUG=release."""
        if isinstance(value, str) and value.strip().lower() in {"release", "production", "prod"}:
            return False
        return value

    def is_production(self) -> bool:
        return self.ENV.lower() == "production"

    def get_sender_email(self) -> str:
        return self.SMTP_FROM or self.SMTP_FROM_EMAIL or self.SMTP_USERNAME or self.EMAIL_FROM or "noreply@yojnasetu.gov.in"

    model_config = SettingsConfigDict(
        env_file=os.path.join(PARENT_DIR, ".env") if os.path.exists(os.path.join(PARENT_DIR, ".env")) else ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            url = self.DATABASE_URL.strip()
            # Normalize legacy Heroku/Render postgres:// to standard postgresql://
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            return url
        if self.POSTGRES_SERVER and self.POSTGRES_USER and self.POSTGRES_PASSWORD and self.POSTGRES_DB:
            return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        return f"sqlite:///{DEFAULT_DB_FILE}"

    def validate_production_security(self) -> None:
        """
        Validates critical security invariants when running in production mode.
        """
        if self.is_production():
            if self.SECRET_KEY == "yojnasetu_dev_secret_key_change_in_production_9f8a7b6c5d4e3f2a1b" or len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "CRITICAL SECURITY CONFIGURATION ERROR: Running in production with default or insecure SECRET_KEY. "
                    "You must provide a high-entropy secret of at least 32 characters in the SECRET_KEY environment variable."
                )
            if self.DEBUG:
                self.DEBUG = False


settings = Settings()
settings.validate_production_security()

