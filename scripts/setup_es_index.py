"""Create Elasticsearch papers index. Run: python -m scripts.setup_es_index"""

import asyncio
import sys

from app.config import get_settings
from app.db.elasticsearch import PAPERS_INDEX_MAPPING, close_elasticsearch, get_elasticsearch


async def _wait_for_elasticsearch(client, url: str, attempts: int = 30, delay: float = 2.0) -> None:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            if await client.ping():
                return
        except Exception as exc:
            last_error = exc
        print(f"Waiting for Elasticsearch at {url} ({attempt}/{attempts})…")
        await asyncio.sleep(delay)
    message = f"Elasticsearch not ready at {url}"
    if last_error:
        raise RuntimeError(message) from last_error
    raise RuntimeError(message)


async def main() -> None:
    settings = get_settings()
    client = get_elasticsearch(settings)
    index = settings.elasticsearch_index
    url = settings.elasticsearch_url

    try:
        await _wait_for_elasticsearch(client, url)

        exists = await client.indices.exists(index=index)
        if exists:
            print(f"Index '{index}' already exists.")
            return

        await client.indices.create(
            index=index,
            settings=PAPERS_INDEX_MAPPING["settings"],
            mappings=PAPERS_INDEX_MAPPING["mappings"],
        )
        print(f"Created index '{index}'.")
    except Exception as exc:
        print(
            f"Elasticsearch setup failed for {url} (index: {index})\n"
            f"{type(exc).__name__}: {exc}\n"
            "Ensure Elasticsearch 8.x is running and elasticsearch-py is pinned to 8.x.",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc
    finally:
        await close_elasticsearch()


if __name__ == "__main__":
    asyncio.run(main())
