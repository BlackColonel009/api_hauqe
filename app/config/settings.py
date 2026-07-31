from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "HAUQE Certif"
    environment: str = "development"
    debug: bool = True

    database_url: str

    secret_key: str
    access_token_expire_minutes: int = 30
    mfa_fernet_key: str | None = None
    password_reset_url_template: str | None = None

    timezone: str = "Africa/Lome"

    hauqe_smtp_host: str | None = None
    hauqe_smtp_port: int = 587
    hauqe_smtp_user: str | None = None
    hauqe_smtp_password: str | None = None
    hauqe_smtp_from: str | None = None
    hauqe_smtp_use_tls: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    
    auth_session_minutes: int = 480

    auth_idle_timeout_minutes: int = 30
    
    # ============================================================
    # SECURITE - PROTECTION ANTI-BRUTEFORCE
    # ============================================================

    auth_max_failed_attempts: int = 5

    auth_failure_window_minutes: int = 15

    auth_lockout_minutes: int = 15


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

