from typing import Any, Dict, Optional
import os
from pydantic import PostgresDsn, validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "PickaBook"
    
    POSTGRES_SERVER: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    DATABASE_URL: Optional[str] = None
    
    REDIS_URL: str
    
    # URL Configuration
    # URL Configuration
    # Auto-detect Render URL or default to localhost
    BASE_URL: str = os.getenv("RENDER_EXTERNAL_URL", "http://localhost:8000")

    # Security
    SECRET_KEY: str = "change_me"
    BACKEND_CORS_ORIGINS: list[str] = ["*"] # Default to wildcard, override in Render

    # AI Service Keys
    REPLICATE_API_TOKEN: Optional[str] = None
    AZURE_FACE_KEY: Optional[str] = None
    AZURE_FACE_ENDPOINT: Optional[str] = None
    
    # Frontend
    NEXT_PUBLIC_API_URL: Optional[str] = None

    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"{values.get('POSTGRES_DB') or ''}",
        ).unicode_string()

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"

settings = Settings()
