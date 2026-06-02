from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    debug: bool = True

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "citexis"

    redis_url: str = "redis://localhost:6379/0"

    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_index: str = "papers"

    pinecone_api_key: str = ""
    pinecone_index: str = "citexis-papers"
    pinecone_namespace: str = "papers-abstract"
    # Record field mapped to the index embed model (e.g. text or chunk_text — match field_map)
    pinecone_text_field: str = "text"
    pinecone_rerank_enabled: bool = True
    pinecone_rerank_model: str = "bge-reranker-v2-m3"

    core_api_key: str = ""
    ingestion_enrich_core: bool = True
    ingestion_max_citations: int = 100

    # Hybrid search defaults
    search_top_k_per_source: int = 50
    search_rrf_k: int = 60
    search_fusion_top_n: int = 20
    search_final_top_n: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()
