from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import Settings


class VectorService:
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection_name = settings.collection_name
        self._initialize_collection()
    
    def _initialize_collection(self):
        try:
            self.collection = self.client.get_collection(
                name=self.collection_name
            )
        except Exception:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
    
    async def store_embeddings(self, embedding_results: List[dict]) -> int:
        if not embedding_results:
            return 0
        
        embeddings = [result["embedding"] for result in embedding_results]
        documents = [result["text"] for result in embedding_results]
        metadatas = [result["metadata"] for result in embedding_results]
        ids = [result["chunk_id"] for result in embedding_results]
        
        self.collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        return len(embedding_results)
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        try:
            count = self.collection.count()
            return {
                "document_count": count,
                "collection_name": self.collection_name
            }
        except Exception as e:
            return {"error": str(e)} 