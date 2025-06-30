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
    
    async def search_similar(self, query_embedding: List[float], top_k: int = 5) -> List[dict]:
        """Search for similar documents using embedding similarity."""
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            search_results = []
            if results and results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    result = {
                        "text": doc,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] and results["metadatas"][0] else {},
                        "distance": results["distances"][0][i] if results["distances"] and results["distances"][0] else 0.0
                    }
                    search_results.append(result)
            
            return search_results
        
        except Exception as e:
            raise RuntimeError(f"Failed to search similar documents: {str(e)}") 