from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "RAG Microservice"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # OpenAI Configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    
    # Vector Database Configuration
    chroma_persist_directory: str = "./chroma_db"
    collection_name: str = "documents"
    
    # Document Processing Configuration
    chunk_size: int = 500
    chunk_overlap: int = 100
    
    # Langfuse Observability Configuration
    langfuse_secret_key: str = ""
    langfuse_public_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings() 