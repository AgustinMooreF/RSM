from fastapi import APIRouter, Depends
from app.models.schemas import HealthResponse
from app.core.config import get_settings, Settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse, status_code=200)
async def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        app_name=settings.app_name,
        version=settings.app_version
    ) 