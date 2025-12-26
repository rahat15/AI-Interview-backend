from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # --- Database ---
    mongo_uri: str = Field(env="MONGO_URI")

    # --- LLM / Evaluation ---
    llm_model: Optional[str] = Field(default=None, env="LLM_MODEL")
    groq_api_key: Optional[str] = Field(default=None, env="GROQ_API_KEY")
    evaluation_timeout: int = Field(default=300, env="EVALUATION_TIMEOUT_SECONDS")

    # --- Redis ---
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")

    # --- Security ---
    secret_key: str = Field(default="dev-secret-key", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    # --- API ---
    api_v1_str: str = Field(default="/v1", env="API_V1_STR")
    project_name: str = Field(default="Interview Coach API", env="PROJECT_NAME")
    
    # --- File Upload ---
    upload_dir: str = Field(default="uploads", env="UPLOAD_DIR")
    max_file_size: int = Field(default=10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()