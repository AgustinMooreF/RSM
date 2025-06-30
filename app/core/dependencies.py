from functools import lru_cache
from typing import TYPE_CHECKING

from app.core.config import get_settings

if TYPE_CHECKING:
    from app.services.document_service import DocumentService


@lru_cache()
def get_document_service() -> "DocumentService":
    from app.services.document_service import DocumentService
    settings = get_settings()
    return DocumentService(settings) 