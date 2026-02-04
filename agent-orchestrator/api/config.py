from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    app_name: str = "agent-orchestrator"
    postgres_dsn: str = Field(..., env="POSTGRES_DSN")
    redis_url: str = Field(..., env="REDIS_URL")
    faiss_index_path: str = Field("/data/faiss.index", env="FAISS_INDEX_PATH")
    embedding_dim: int = Field(384, env="EMBEDDING_DIM")
    rate_limit_per_user: int = Field(60, env="RATE_LIMIT_PER_USER")
    rate_limit_per_task: int = Field(30, env="RATE_LIMIT_PER_TASK")


settings = Settings()
