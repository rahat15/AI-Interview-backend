from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    APP_NAME: str = "AI Interview Coach"
    APP_ENV: str = "prod"  # dev | staging | prod
    API_V1_PREFIX: str = "/api/v1"

    # LLM default provider/model read by evaluations/llm_scorer.py
    LLM_PROVIDER: str = "groq"
    LLM_MODEL: str = "llama3-8b-8192"

    # Provider keys (only the ones you use need to be set in .env)
    GROQ_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    HUGGINGFACEHUB_API_TOKEN: str | None = None

    # CORS
    CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["*"])  # tighten in prod

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
