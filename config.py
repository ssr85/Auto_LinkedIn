"""Configuration management for the LinkedIn content automation system."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False
    )

    # Client identity (optional — used for multi-client mode)
    client_name: Optional[str] = None

    # API Keys
    openai_api_key: str
    anthropic_api_key: Optional[str] = None
    serper_api_key: Optional[str] = None

    # Trello Configuration
    trello_api_key: str
    trello_token: str
    trello_board_id: str
    trello_topics_list_id: str      # List 1: Topics
    trello_approved_topics_id: str   # List 2: Approved Topics
    trello_content_approval_id: str  # List 3: Content Approval
    trello_approved_content_id: str  # List 4: Approved Content
    trello_archive_list_id: str      # List 5: Content Archive

    # LinkedIn Configuration
    linkedin_client_id: Optional[str] = None
    linkedin_client_secret: Optional[str] = None
    linkedin_access_token: str
    linkedin_refresh_token: Optional[str] = None
    linkedin_user_id: str

    # Research Configuration
    target_url: str
    target_industry: str
    research_frequency_hours: int = 24

    # AI Model Configuration
    ai_model: str = "gpt-4-turbo-preview"

    # Logging
    log_level: str = "INFO"

    # System Configuration
    max_topics_per_research: int = 5
    max_retries: int = 3
    content_min_length: int = 500
    content_max_length: int = 3000

    # Polling Configuration
    approval_wait_time_minutes: int = 5
    approval_retry_count: int = 5


# Global settings instance (single-client / backward-compatible default)
settings = Settings()


def load_client_settings(env_file: str, client_name: str) -> "Settings":
    """Load settings from a client-specific env file.

    Args:
        env_file: Path to the client's .env file (e.g. 'clients/acme.env')
        client_name: Logical name used for logging and log directories

    Returns:
        A fully-validated Settings instance for that client
    """
    return Settings(_env_file=env_file, client_name=client_name)  # type: ignore[call-arg]
