from functools import lru_cache
from app.core.config import get_settings
from app.services.document_service import DocumentService


@lru_cache()
def get_document_service() -> DocumentService:
    settings = get_settings()
    return DocumentService(settings) 