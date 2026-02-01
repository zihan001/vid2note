"""
Configuration management using pydantic-settings
"""

from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # IBM watsonx.ai
    WATSONX_API_KEY: Optional[str] = None
    WATSONX_PROJECT_ID: Optional[str] = None
    WATSONX_URL: str = "https://us-south.ml.cloud.ibm.com"
    
    # OpenAI (fallback/testing)
    OPENAI_API_KEY: Optional[str] = None
    
    # Application
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Storage
    STORAGE_ROOT: Path = Path("./storage")
    VIDEO_STORAGE: Path = Path("./storage/videos")
    TRANSCRIPT_STORAGE: Path = Path("./storage/transcripts")
    FRAME_STORAGE: Path = Path("./storage/frames")
    PDF_STORAGE: Path = Path("./storage/pdfs")
    
    # Database
    DATABASE_URL: str = "sqlite:///./vid2note.db"
    
    # Processing
    MAX_VIDEO_SIZE_MB: int = 500
    MAX_TRANSCRIPT_SIZE_MB: int = 10
    FRAME_EXTRACTION_INTERVAL: int = 2
    MAX_CONCURRENT_JOBS: int = 3
    
    # LLM
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_MAX_RETRIES: int = 5
    LLM_TIMEOUT_SECONDS: int = 30
    CONFIDENCE_THRESHOLD: int = 75
    
    # PDF
    PDF_MAX_IMAGES: int = 12
    PDF_IMAGE_WIDTH: int = 1800
    PDF_THUMBNAIL_WIDTH: int = 480
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
