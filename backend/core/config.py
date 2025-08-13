from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    PROJECT_TITLE: str = "RSVP"
    PROJECT_DESCRIPTION: str = "Event RSVP API"
    PROJECT_VERSION: str = "0.1.0"

    SESSION_SECRET_KEY: str

    POSTGRES_USER: str
    POSTGRES_DATABASE: str
    POSTGRES_HOST: str
    POSTGRES_PASSWORD: str
    POSTGRES_PORT: int

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # GOOGLE_CLIENT_ID: str
    # GOOGLE_CLIENT_SECRET: str
    # GOOGLE_REDIRECT_URI: str

    EMAIL_ENABLED: bool = True
    SMTP_SERVER: str
    SMTP_PORT: int
    SMTP_USE_TLS: bool = False
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    SMTP_FROM_EMAIL: str
    SMTP_FROM_NAME: str

    RATE_LIMITING_ENABLED: bool = True
    RATE_LIMIT_STORAGE_URI: str = "memory://"  # For Redis: redis://localhost:6379
    RATE_LIMIT_DEFAULT: list = ["100/minute"]

    OTP_EXPIRE_MINUTES: int = 10

    FRONTEND_URL: str
    UPLOAD_DIR: str = "uploads"

    model_config = SettingsConfigDict(env_file="backend/.env")


settings: Settings = Settings()
