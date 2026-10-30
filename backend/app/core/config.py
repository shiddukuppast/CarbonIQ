from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables or .env file.
    """
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    APP_NAME: str = "CarbonIQ API"
    APP_VERSION: str = "1.0.0"

    # MongoDB Atlas Settings
    MONGODB_URI: str = Field(default="mongodb://localhost:27017")
    MONGODB_DATABASE: str = Field(default="carboniq_dev")

    # JWT Authentication
    JWT_SECRET_KEY: str = Field(
        default="carboniq-hackathon-development-secret-key-32bytes-min"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # CORS Settings
    FRONTEND_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Groq LLM Provider Settings (Primary)
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "qwen/qwen3.8-27b"

    # Backward-compatibility fallback settings
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL: Optional[str] = None

    @property
    def effective_groq_api_key(self) -> Optional[str]:
        return self.GROQ_API_KEY or self.LLM_API_KEY

    @property
    def effective_groq_model(self) -> str:
        return self.GROQ_MODEL or self.LLM_MODEL or "qwen/qwen3.8-27b"

    # ML Model Configuration
    ML_MODEL_PATH: str = "carboniq_emissions_model.joblib"
    ML_METADATA_PATH: str = "metrics.json"

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.FRONTEND_ORIGINS.split(",") if origin.strip()]


settings = Settings()
