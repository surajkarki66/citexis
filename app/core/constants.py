from enum import StrEnum


class EmbeddingStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


class InteractionType(StrEnum):
    VIEW = "view"
    SAVE = "save"
    CLICK = "click"
    RATING = "rating"


class RecommendationReason(StrEnum):
    SEMANTIC = "semantically similar"
    CITATION = "cited together"
    COLLABORATIVE = "readers also saved"
