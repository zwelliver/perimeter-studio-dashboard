from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings using Pydantic BaseSettings."""

    # Environment
    environment: str = "development"

    # App settings
    app_name: str = "Studio Command Center"
    app_version: str = "1.0.0"

    # File storage
    reports_dir: str = "Reports"

    # Cache settings
    cache_duration: int = 300  # 5 minutes in seconds

    # Scheduler settings
    background_refresh_interval: int = 5  # minutes

    # Asana API tokens
    asana_pat_scorer: Optional[str] = None
    asana_pat_backdrop: Optional[str] = None

    # AI API keys
    grok_api_key: Optional[str] = None
    stable_diffusion_api_key: Optional[str] = None
    replicate_api_token: Optional[str] = None
    calendly_api_key: Optional[str] = None

    # Asana Custom Field GIDs
    film_date_field_gid: Optional[str] = None
    task_progress_field_gid: Optional[str] = None
    needs_scheduling_option_gid: Optional[str] = None

    # Email Alert Configuration
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_username: Optional[str] = None

    # Production project GIDs
    production_project_gids: Optional[str] = None

    # Forecast Alert Email Configuration
    alert_email_from: Optional[str] = None
    alert_email_to: Optional[str] = None

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()