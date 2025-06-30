import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings, Settings
from app.api.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # 🟢 STARTUP PHASE
    print("🚀 Starting RAG Microservice...")
    settings = get_settings()
    
    try:
        # Create necessary directories
        os.makedirs(settings.chroma_persist_directory, exist_ok=True)
        print(f"✅ ChromaDB directory ready: {settings.chroma_persist_directory}")
        
        # Environment validation
        if not settings.openai_api_key:
            print("⚠️  WARNING: OpenAI API key not set. Document ingestion will fail.")
            print("   Set OPENAI_API_KEY environment variable to enable full functionality.")
        else:
            print("✅ OpenAI API key configured")
        
        # Store startup time for metrics
        import time
        app.state.start_time = time.time()
        app.state.request_count = 0
        
        print(f"🎉 {settings.app_name} v{settings.app_version} started successfully!")
        print(f"📊 API Documentation: http://localhost:8000/docs")
        
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        raise  # This prevents the app from starting
    
    # 🎯 APPLICATION RUNS HERE
    yield
    
    # 🔴 SHUTDOWN PHASE
    print("🛑 Shutting down RAG Microservice...")
    
    try:
        # Calculate uptime
        uptime = time.time() - app.state.start_time
        print(f"📈 Application ran for {uptime:.2f} seconds")
        print(f"📊 Handled {getattr(app.state, 'request_count', 0)} requests")
        
        # Here you could:
        # - Close database connections
        # - Cancel background tasks  
        # - Save application state
        # - Flush logs or metrics
        
        print("✅ Graceful shutdown completed")
        
    except Exception as e:
        print(f"⚠️  Shutdown warning: {e}")
        # Don't raise - shutdown should complete
    
    print("👋 RAG Microservice stopped")


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
        allow_origins=["*"],  # Configure based on your needs
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API router
    app.include_router(api_router, prefix="/api/v1")
    
    return app


app = create_app()


@app.get("/")
async def root(settings: Settings = Depends(get_settings)):
    """Root endpoint with enhanced information."""
    # Increment request counter (example of using app.state)
    if hasattr(app.state, 'request_count'):
        app.state.request_count += 1
    
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "status": "ready",
        "features": [
            "Document ingestion (text, HTML, markdown, PDF)",
            "File upload support (PDF)",
            "Vector storage with ChromaDB",
            "OpenAI embeddings"
        ],
        "endpoints": {
            "health": "/api/v1/health",
            "ingest_text": "/api/v1/ingest",
            "ingest_file": "/api/v1/ingest/file",
            "docs": "/docs",
            "openapi": "/openapi.json"
        }
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