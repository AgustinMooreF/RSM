import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings, Settings
from app.core.dependencies import get_observability_service
from app.api.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with observability."""
    settings = get_settings()
    
    os.makedirs(settings.chroma_persist_directory, exist_ok=True)
    
    # Initialize observability service
    observability_service = get_observability_service()
    
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"Chroma DB directory: {settings.chroma_persist_directory}")
    
    if not settings.openai_api_key:
        print("⚠️  WARNING: OpenAI API key not set. Document ingestion will fail.")
    
    if settings.langfuse_secret_key and settings.langfuse_public_key:
        print("✅ Langfuse observability enabled")
        observability_service.log_metrics("application_startup", {
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "observability_enabled": True
        })
    else:
        print("⚠️  Langfuse observability disabled (keys not provided)")
        print("   Set LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY environment variables to enable")
    
    yield

    print("Shutting down RAG Microservice...")
    
    if observability_service:
        print("Flushing observability events...")
        observability_service.flush()
        observability_service.log_metrics("application_shutdown", {
            "app_name": settings.app_name,
            "graceful_shutdown": True
        })
        observability_service.flush()
    
    print("Shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="A Python-based Retrieval-Augmented Generation (RAG) microservice",
        lifespan=lifespan
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(api_router, prefix="/api/v1")
    
    return app


app = create_app()


@app.get("/")
async def root(settings: Settings = Depends(get_settings)):
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "status": "ready",
        "features": [
            "Document ingestion (text, HTML, markdown, PDF)",
            "File upload support (PDF)",
            "Vector storage with ChromaDB",
            "OpenAI embeddings"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    ) 