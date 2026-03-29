"""Configurações centrais da aplicação Carbon Verify."""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configurações do aplicativo."""
    APP_NAME: str = "Carbon Verify"
    APP_VERSION: str = "1.0.0-mvp"
    APP_DESCRIPTION: str = "Plataforma B2B SaaS de verificação e due diligence de créditos de carbono"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./carbon_verify.db")
    
    # JWT Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "carbon-verify-mvp-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # CORS
    CORS_ORIGINS: list[str] = ["*"]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
