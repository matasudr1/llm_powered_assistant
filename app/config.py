"""
Configuration settings for the Data Assistant API.
Supports both OpenAI and Ollama backends.
"""

from pydantic_settings import BaseSettings
from typing import Literal
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # API Configuration
    app_name: str = "Data Assistant API"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # LLM Configuration
    llm_provider: Literal["openai", "ollama"] = "openai"
    
    # OpenAI Settings
    openai_api_key: str = ""
    openai_model: str = "gpt-3.5-turbo"
    
    # Ollama Settings (free, local)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama2"
    
    # Database Settings
    database_url: str = "sqlite:///./data/sample.db"
    
    # Rate Limiting
    max_requests_per_minute: int = 60
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
