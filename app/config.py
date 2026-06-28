from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All values must be set in `.env`."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str
    debug: bool

    mongodb_uri: str
    mongodb_db: str

    redis_url: str

    elasticsearch_url: str
    elasticsearch_index: str

    pinecone_api_key: str
    pinecone_index: str
    pinecone_namespace: str
    pinecone_text_field: str
    pinecone_rerank_enabled: bool
    pinecone_rerank_model: str

    core_api_key: str
    ingestion_enrich_core: bool
    ingestion_max_citations: int

    json_import_max_bytes: int
    json_import_max_papers: int

    search_top_k_per_source: int
    search_rrf_k: int
    search_fusion_top_n: int
    search_final_top_n: int

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 1440

    auth_admin_email: str = ""
    auth_admin_password: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
