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

    # API Keys
    openai_api_key: str
    anthropic_api_key: Optional[str] = None

    # Trello Configuration
    trello_api_key: str
    trello_token: str
    trello_board_id: str
    trello_topics_list_id: str
    trello_content_list_id: str

    # LinkedIn Configuration
    linkedin_client_id: Optional[str] = None
    linkedin_client_secret: Optional[str] = None
    linkedin_access_token: str
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


# Global settings instance
settings = Settings()
