"""
Configuration management
"""
from pydantic import BaseSettings, PostgresDsn, validator
from typing import Optional, Dict, Any
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: Optional[str] = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://user:pass@localhost/ghg_db"
    )
    
    # Testing
    TESTING: bool = os.getenv("TESTING", "false").lower() == "true"
    TEST_DATABASE_URL: Optional[str] = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://user:pass@localhost/ghg_test"
    )
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "GHG Protocol Calculator"
    
    # GHG Calculation Settings
    DEFAULT_EMISSION_FACTORS_YEAR: int = 2024
    CALCULATION_CACHE_TTL: int = 3600  # 1 hour
    
    # External APIs
    EPA_API_KEY: Optional[str] = os.getenv("EPA_API_KEY")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

def get_settings() -> Settings:
    return Settings()