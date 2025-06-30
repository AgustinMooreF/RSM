from fastapi import APIRouter
from app.api.endpoints import health, ingest, query

api_router = APIRouter()


api_router.include_router(health.router, tags=["health"])
api_router.include_router(ingest.router, tags=["ingestion"])
api_router.include_router(query.router, tags=["query"])