import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Configuración global del sistema"""
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    openai_temperature: float = Field(default=0.0, env="OPENAI_TEMPERATURE")
    
    # MongoDB Configuration
    mongodb_url: str = Field(default="mongodb://localhost:27017", env="MONGODB_URL")
    mongodb_db_name: str = Field(default="onboarding_system", env="MONGODB_DB_NAME")
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    encrypt_key: str = Field(..., env="ENCRYPT_KEY")
    
    # Performance
    agent_response_timeout: int = Field(default=2, env="AGENT_RESPONSE_TIMEOUT")
    notification_timeout: int = Field(default=60, env="NOTIFICATION_TIMEOUT")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/onboarding_system.log", env="LOG_FILE")
    
    # Langfuse Configuration
    langfuse_secret_key: str = Field(default="", env="LANGFUSE_SECRET_KEY")
    langfuse_public_key: str = Field(default="", env="LANGFUSE_PUBLIC_KEY")
    langfuse_base_url: str = Field(default="https://us.cloud.langfuse.com", env="LANGFUSE_BASE_URL")
    langfuse_enabled: bool = Field(default=True, env="LANGFUSE_ENABLED")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Instancia global de configuración
settings = Settings()