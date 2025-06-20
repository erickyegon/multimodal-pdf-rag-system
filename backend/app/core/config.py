from pydantic_settings import BaseSettings
from pydantic import validator
from typing import Optional, List
import os
from pathlib import Path

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Multimodal PDF RAG System"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Advanced multimodal PDF analysis with AI"
    
    # EURI AI Configuration
    EURI_API_KEY: Optional[str] = None
    EURI_MODEL: str = "gpt-4.1-nano"
    EURI_EMBEDDING_MODEL: str = "text-embedding-3-large"
    EURI_MAX_RETRIES: int = 3
    EURI_TIMEOUT: int = 30
    
    # Vector Database Configuration
    VECTOR_DB_TYPE: str = "chroma"  # or "faiss"
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"
    FAISS_INDEX_PATH: str = "./faiss_index"
    
    # Processing Configuration
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    MAX_TOKENS: int = 2000
    TEMPERATURE: float = 0.1
    
    # File Configuration
    UPLOAD_DIR: str = "./uploads"
    PROCESSED_DIR: str = "./processed"
    MAX_FILE_SIZE: int = 104857600  # 100MB
    ALLOWED_FILE_TYPES: List[str] = [".pdf"]
    
    # Database Configuration
    DATABASE_URL: str = "sqlite:///./pdf_rag.db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis Configuration (optional)
    REDIS_URL: Optional[str] = None
    REDIS_EXPIRE_TIME: int = 3600  # 1 hour
    
    # Security Configuration
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Query Configuration
    MAX_QUERY_LENGTH: int = 2000
    MAX_SOURCES_PER_QUERY: int = 20
    DEFAULT_K_SOURCES: int = 5
    
    # Processing Limits
    MAX_CONCURRENT_UPLOADS: int = 5
    PROCESSING_TIMEOUT: int = 1800  # 30 minutes
    
    # Monitoring Configuration
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    LOG_LEVEL: str = "INFO"
    
    # LangChain Configuration
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_ENDPOINT: Optional[str] = None
    LANGCHAIN_API_KEY: Optional[str] = None
    
    # Chart Generation Configuration
    CHART_WIDTH: int = 800
    CHART_HEIGHT: int = 600
    CHART_DPI: int = 100
    
    # Analytics Configuration
    ENABLE_ANALYTICS: bool = True
    ANALYTICS_RETENTION_DAYS: int = 30
    
    # Development Configuration
    DEBUG: bool = False
    TESTING: bool = False
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    @validator('EURI_API_KEY')
    def validate_euri_api_key(cls, v):
        if v and len(v) < 10:
            raise ValueError('EURI_API_KEY must be at least 10 characters long')
        return v

    class Config:
        env_file = "../.env"  # Look for .env in parent directory
        case_sensitive = True
        
    def get_upload_path(self) -> Path:
        """Get upload directory path"""
        path = Path(self.UPLOAD_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_processed_path(self) -> Path:
        """Get processed files directory path"""
        path = Path(self.PROCESSED_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_chroma_path(self) -> Path:
        """Get Chroma database path"""
        path = Path(self.CHROMA_PERSIST_DIRECTORY)
        path.mkdir(parents=True, exist_ok=True)
        return path

# Environment-specific configurations
class DevelopmentSettings(Settings):
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    ALLOWED_ORIGINS: List[str] = ["*"]

class ProductionSettings(Settings):
    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"
    # Override with production values
    pass

class TestingSettings(Settings):
    TESTING: bool = True
    DATABASE_URL: str = "sqlite:///./test.db"
    UPLOAD_DIR: str = "./test_uploads"

def get_settings() -> Settings:
    """Get settings based on environment"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()

settings = get_settings()