"""Create Elasticsearch papers index. Run: python -m scripts.setup_es_index"""

import asyncio
import sys

from app.config import get_settings
from app.db.elasticsearch import PAPERS_INDEX_MAPPING, close_elasticsearch, get_elasticsearch


async def main() -> None:
    settings = get_settings()
    client = get_elasticsearch(settings)
    index = settings.elasticsearch_index

    try:
        exists = await client.indices.exists(index=index)
        if exists:
            print(f"Index '{index}' already exists.")
            return

        await client.indices.create(index=index, body=PAPERS_INDEX_MAPPING)
        print(f"Created index '{index}'.")
    except Exception as exc:
        print(
            f"Could not reach Elasticsearch at {settings.elasticsearch_url}\n"
            "Start Elasticsearch first, then run this script again.\n"
            "Example (Docker):\n"
            '  docker run -d --name citexis-elasticsearch -p 9200:9200 \\\n'
            '    -e "discovery.type=single-node" \\\n'
            '    -e "xpack.security.enabled=false" \\\n'
            "    docker.elastic.co/elasticsearch/elasticsearch:8.15.0\n",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc
    finally:
        await close_elasticsearch()


if __name__ == "__main__":
    asyncio.run(main())
