"""Application settings loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed configuration with defaults from CONFIGURATION.md."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="grounded-research-desk", alias="APP_NAME")
    app_env: Literal["development", "production"] = Field(
        default="development",
        alias="APP_ENV",
    )
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    api_host: str = Field(default="127.0.0.1", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")

    database_url: str = Field(
        default="sqlite:///./data/grounded_research.db",
        alias="DATABASE_URL",
    )

    max_upload_bytes: int = Field(default=5_242_880, alias="MAX_UPLOAD_BYTES")
    allowed_upload_extensions: str = Field(
        default=".txt,.md",
        alias="ALLOWED_UPLOAD_EXTENSIONS",
    )

    embedding_model_name: str = Field(
        default="all-MiniLM-L6-v2",
        alias="EMBEDDING_MODEL_NAME",
    )
    embedding_dimension: int = Field(default=384, alias="EMBEDDING_DIMENSION")
    embedding_device: Literal["cpu", "cuda"] = Field(
        default="cpu",
        alias="EMBEDDING_DEVICE",
    )

    chunk_size_chars: int = Field(default=800, alias="CHUNK_SIZE_CHARS")
    chunk_overlap_chars: int = Field(default=120, alias="CHUNK_OVERLAP_CHARS")

    retrieval_top_k: int = Field(default=5, alias="RETRIEVAL_TOP_K")
    min_similarity_score: float = Field(default=0.25, alias="MIN_SIMILARITY_SCORE")
    evidence_min_lexical_overlap: float = Field(
        default=0.15,
        alias="EVIDENCE_MIN_LEXICAL_OVERLAP",
    )

    llm_provider: Literal["mock", "ollama"] = Field(default="mock", alias="LLM_PROVIDER")
    ollama_base_url: str = Field(
        default="http://127.0.0.1:11434",
        alias="OLLAMA_BASE_URL",
    )
    ollama_model: str = Field(default="llama3.2", alias="OLLAMA_MODEL")
    generation_timeout_seconds: int = Field(
        default=60,
        alias="GENERATION_TIMEOUT_SECONDS",
    )

    agent_enabled: bool = Field(default=False, alias="AGENT_ENABLED")
    agent_max_tool_calls: int = Field(default=8, alias="AGENT_MAX_TOOL_CALLS")
    agent_max_wall_clock_seconds: int = Field(
        default=120,
        alias="AGENT_MAX_WALL_CLOCK_SECONDS",
    )

    demo_mode: bool = Field(default=False, alias="DEMO_MODE")

    embedding_provider: Literal["fake", "local"] = Field(
        default="fake",
        alias="EMBEDDING_PROVIDER",
    )
    data_dir: str = Field(default="./data", alias="DATA_DIR")
    upload_dir: str = Field(default="./data/uploads", alias="UPLOAD_DIR")
    cors_origins: str = Field(
        default="http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:4173,http://localhost:4173",
        alias="CORS_ORIGINS",
    )

    app_version: str = Field(default="0.1.0", exclude=True)

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        return value.upper()

    @model_validator(mode="after")
    def validate_cross_field_rules(self) -> "Settings":
        if self.chunk_overlap_chars >= self.chunk_size_chars:
            msg = "CHUNK_OVERLAP_CHARS must be less than CHUNK_SIZE_CHARS"
            raise ValueError(msg)
        if self.retrieval_top_k < 1:
            msg = "RETRIEVAL_TOP_K must be at least 1"
            raise ValueError(msg)
        return self

    @property
    def allowed_extensions_list(self) -> list[str]:
        return [
            ext.strip()
            for ext in self.allowed_upload_extensions.split(",")
            if ext.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()
