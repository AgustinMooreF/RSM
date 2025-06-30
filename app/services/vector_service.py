from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import Settings


class VectorService:
    """Service for vector storage and similarity search with Langfuse observability."""
    
    def __init__(self, settings: Settings, observability_service=None):
        self.settings = settings
        self.observability_service = observability_service
        
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection_name = settings.collection_name
        self._initialize_collection()
    
    def _initialize_collection(self):
        """Initialize the ChromaDB collection."""
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
        """Store embeddings in the vector database with observability."""
        if self.observability_service:
            async with self.observability_service.trace_operation(
                "vector_storage",
                embedding_count=len(embedding_results),
                collection_name=self.collection_name
            ):
                return await self._store_embeddings_impl(embedding_results)
        else:
            return await self._store_embeddings_impl(embedding_results)
    
    async def _store_embeddings_impl(self, embedding_results: List[dict]) -> int:
        """Internal implementation of embedding storage."""
        if not embedding_results:
            return 0
        
        try:
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
            
            if self.observability_service:
                self.observability_service.log_metrics("vector_storage", {
                    "embeddings_stored": len(embedding_results),
                    "collection_name": self.collection_name,
                    "average_document_length": sum(len(doc) for doc in documents) / len(documents) if documents else 0
                })
            
            return len(embedding_results)
            
        except Exception as e:
            raise RuntimeError(f"Failed to store embeddings: {str(e)}")
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics with observability."""
        if self.observability_service:
            async with self.observability_service.trace_operation(
                "collection_stats_retrieval",
                collection_name=self.collection_name
            ):
                return await self._get_collection_stats_impl()
        else:
            return await self._get_collection_stats_impl()
    
    async def _get_collection_stats_impl(self) -> Dict[str, Any]:
        """Internal implementation of collection stats retrieval."""
        try:
            count = self.collection.count()
            stats = {
                "document_count": count,
                "collection_name": self.collection_name
            }
            
            if self.observability_service:
                self.observability_service.log_metrics("collection_stats", stats)
            
            return stats
        except Exception as e:
            return {"error": str(e)}
    
    async def search_similar(self, query_embedding: List[float], top_k: int = 5) -> List[dict]:
        """Search for similar documents using embedding similarity with observability."""
        if self.observability_service:
            async with self.observability_service.trace_operation(
                "similarity_search",
                top_k=top_k,
                collection_name=self.collection_name,
                embedding_dimension=len(query_embedding) if query_embedding else 0
            ):
                return await self._search_similar_impl(query_embedding, top_k)
        else:
            return await self._search_similar_impl(query_embedding, top_k)
    
    async def _search_similar_impl(self, query_embedding: List[float], top_k: int) -> List[dict]:
        """Internal implementation of similarity search."""
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
            
            if self.observability_service:
                self.observability_service.log_metrics("similarity_search", {
                    "query_embedding_dimension": len(query_embedding) if query_embedding else 0,
                    "top_k_requested": top_k,
                    "results_returned": len(search_results),
                    "collection_name": self.collection_name,
                    "average_distance": sum(r["distance"] for r in search_results) / len(search_results) if search_results else 0
                })
            
            return search_results
        
        except Exception as e:
            raise RuntimeError(f"Failed to search similar documents: {str(e)}") 