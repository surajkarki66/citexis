__all__ = ["HybridSearchService"]


def __getattr__(name: str):
    if name == "HybridSearchService":
        from app.services.search.hybrid import HybridSearchService

        return HybridSearchService
    raise AttributeError(name)
