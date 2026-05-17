"""Create Elasticsearch papers index. Run: python -m scripts.setup_es_index"""

import asyncio

from app.config import get_settings
from app.db.elasticsearch import PAPERS_INDEX_MAPPING, get_elasticsearch


async def main() -> None:
    settings = get_settings()
    client = get_elasticsearch(settings)
    index = settings.elasticsearch_index

    exists = await client.indices.exists(index=index)
    if exists:
        print(f"Index '{index}' already exists.")
        return

    await client.indices.create(index=index, body=PAPERS_INDEX_MAPPING)
    print(f"Created index '{index}'.")


if __name__ == "__main__":
    asyncio.run(main())
