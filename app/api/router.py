from fastapi import APIRouter
from app.api.endpoints import health, ingest

api_router = APIRouter()


api_router.include_router(health.router, tags=["health"])
api_router.include_router(ingest.router, tags=["ingestion"])