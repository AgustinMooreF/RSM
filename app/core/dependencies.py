from functools import lru_cache
from typing import TYPE_CHECKING

from app.core.config import get_settings

if TYPE_CHECKING:
    from app.services.document_service import DocumentService
    from app.services.observability_service import ObservabilityService


@lru_cache()
def get_observability_service() -> "ObservabilityService":
    from app.services.observability_service import ObservabilityService
    settings = get_settings()
    return ObservabilityService(settings)


@lru_cache()
def get_document_service() -> "DocumentService":
    from app.services.document_service import DocumentService
    settings = get_settings()
    observability_service = get_observability_service()
    return DocumentService(settings, observability_service) 