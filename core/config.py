from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Settings
    api_v1_str: str = Field(default="/v1", env="API_V1_STR")
    project_name: str = Field(default="Interview Coach API", env="PROJECT_NAME")
    version: str = Field(default="1.0.0")
    debug: bool = Field(default=False, env="DEBUG")
    
    # CORS
    backend_cors_origins: List[str] = Field(
        default=["http://localhost:3000"], 
        env="BACKEND_CORS_ORIGINS"
    )
    
    # Security
    secret_key: str = Field(env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30, 
        env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    
    # Database
    database_url: str = Field(env="DATABASE_URL")
    
    # Redis
    redis_url: str = Field(env="REDIS_URL")
    
    # Sentry
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    
    # Embeddings
    embeddings_model: str = Field(default="local", env="EMBEDDINGS_MODEL")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    cohere_api_key: Optional[str] = Field(default=None, env="COHERE_API_KEY")
    
    # File Storage
    upload_dir: str = Field(default="uploads")
    max_file_size: int = Field(default=10 * 1024 * 1024)  # 10MB
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60)
    
    # Interview Settings
    max_questions_per_session: int = Field(default=20)
    max_follow_ups_per_question: int = Field(default=3)
    
    # Evaluation
    evaluation_timeout: int = Field(default=300)  # 5 minutes
    
    class Config:
        env_file = ".env"
        extra = "allow"


# Global settings instance
settings = Settings()
