from elasticsearch import AsyncElasticsearch

from app.config import Settings

_client: AsyncElasticsearch | None = None

# Run once: python -m scripts.setup_es_index
PAPERS_INDEX_MAPPING = {
    "settings": {
        "analysis": {
            "analyzer": {
                "scientific_text": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "english_stop", "english_stemmer"],
                }
            },
            "filter": {
                "english_stop": {"type": "stop", "stopwords": "_english_"},
                "english_stemmer": {"type": "stemmer", "language": "english"},
            },
        }
    },
    "mappings": {
        "properties": {
            "paper_id": {"type": "keyword"},
            "title": {"type": "text", "analyzer": "scientific_text"},
            "abstract": {"type": "text", "analyzer": "scientific_text"},
            "authors": {"type": "keyword"},
            "year": {"type": "integer"},
            "venue": {"type": "keyword"},
            "tags": {"type": "keyword"},
            "citation_count": {"type": "integer"},
        }
    },
}


def get_elasticsearch(settings: Settings) -> AsyncElasticsearch:
    global _client
    if _client is None:
        _client = AsyncElasticsearch(settings.elasticsearch_url, request_timeout=30)
    return _client


async def close_elasticsearch() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None
