from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_environment: str = "development"
    database_url: str = "sqlite:///./clientops.db"
    allowed_cors_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    upload_directory: Path = Path("uploads")
    frontend_directory: Path | None = None
    api_prefix: str = ""
    max_upload_size_bytes: int = Field(10 * 1024 * 1024, ge=1)
    openrouter_api_key: str | None = None
    openrouter_model: str = "openai/gpt-4o-mini"
    pinecone_api_key: str | None = None
    pinecone_index_name: str | None = None
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_provider: str = "sentence_transformers"
    pinecone_embedding_model: str = "llama-text-embed-v2"
    retrieval_top_k: int = Field(4, ge=1, le=20)
    retrieval_min_score: float = Field(0.25, ge=-1, le=1)
    provider_timeout_seconds: float = Field(30, ge=1, le=120)
    demo_mode: bool = False
    serverless_demo_bootstrap: bool = False
    allow_session_uploads: bool = False
    demo_chat_hourly_limit: int = Field(40, ge=1, le=1000)
    log_level: str = "INFO"

    @field_validator("allowed_cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: object) -> object:
        if isinstance(value, str) and not value.startswith("["):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("frontend_directory", mode="before")
    @classmethod
    def parse_optional_path(cls, value: object) -> object:
        return None if value == "" else value

    @field_validator("api_prefix")
    @classmethod
    def normalise_api_prefix(cls, value: str) -> str:
        clean = value.strip()
        if not clean or clean == "/":
            return ""
        return f"/{clean.strip('/')}"

    @property
    def is_production(self) -> bool:
        return self.app_environment.lower() == "production"

    def validate_production_integrations(self) -> None:
        missing = []
        if not self.openrouter_api_key:
            missing.append("OPENROUTER_API_KEY")
        if not self.pinecone_api_key:
            missing.append("PINECONE_API_KEY")
        if not self.pinecone_index_name:
            missing.append("PINECONE_INDEX_NAME")
        if self.is_production and missing:
            raise RuntimeError(f"Missing required production configuration: {', '.join(missing)}")


@lru_cache
def get_settings() -> Settings:
    return Settings()
