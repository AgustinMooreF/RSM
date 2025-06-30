from typing import List
import openai
from app.core.config import Settings
from app.utils.text_splitter import DocumentChunk


class EmbeddingService:
    """Service for generating embeddings with Langfuse observability."""
    
    def __init__(self, settings: Settings, observability_service=None):
        self.settings = settings
        self.observability_service = observability_service
        
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key is required")
        
        if observability_service and observability_service.get_instrumented_openai():
            self.client = observability_service.get_instrumented_openai()
        else:
            self.client = openai.OpenAI(api_key=settings.openai_api_key)
        
        self.model = settings.openai_embedding_model
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate a single embedding with observability."""
        if self.observability_service:
            async with self.observability_service.trace_operation(
                "embedding_generation",
                model=self.model,
                text_length=len(text)
            ):
                return await self._generate_embedding_impl(text)
        else:
            return await self._generate_embedding_impl(text)
    
    async def _generate_embedding_impl(self, text: str) -> List[float]:
        """Internal implementation of embedding generation."""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            
            if self.observability_service:
                self.observability_service.log_metrics("embedding_generation", {
                    "text_length": len(text),
                    "model": self.model,
                    "embedding_dimensions": len(response.data[0].embedding) if response.data else 0
                })
            
            return response.data[0].embedding
        except Exception as e:
            raise RuntimeError(f"Failed to generate embedding: {str(e)}")
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate batch embeddings with observability."""
        if self.observability_service:
            async with self.observability_service.trace_operation(
                "batch_embedding_generation",
                model=self.model,
                batch_size=len(texts),
                total_text_length=sum(len(text) for text in texts)
            ):
                return await self._generate_embeddings_batch_impl(texts)
        else:
            return await self._generate_embeddings_batch_impl(texts)
    
    async def _generate_embeddings_batch_impl(self, texts: List[str]) -> List[List[float]]:
        """Internal implementation of batch embedding generation."""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            
            if self.observability_service:
                self.observability_service.log_metrics("batch_embedding_generation", {
                    "batch_size": len(texts),
                    "total_text_length": sum(len(text) for text in texts),
                    "average_text_length": sum(len(text) for text in texts) / len(texts) if texts else 0,
                    "model": self.model,
                    "embeddings_created": len(response.data) if response.data else 0
                })
            
            return [item.embedding for item in response.data]
        except Exception as e:
            raise RuntimeError(f"Failed to generate batch embeddings: {str(e)}")
    
    async def embed_chunks(self, chunks: List[DocumentChunk]) -> List[dict]:
        """Embed document chunks with observability."""
        if self.observability_service:
            async with self.observability_service.trace_operation(
                "document_chunks_embedding",
                chunk_count=len(chunks),
                total_text_length=sum(len(chunk.text) for chunk in chunks)
            ):
                return await self._embed_chunks_impl(chunks)
        else:
            return await self._embed_chunks_impl(chunks)
    
    async def _embed_chunks_impl(self, chunks: List[DocumentChunk]) -> List[dict]:
        """Internal implementation of chunk embedding."""
        texts = [chunk.text for chunk in chunks]
        
        batch_size = 100
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_embeddings = await self.generate_embeddings_batch(batch_texts)
            all_embeddings.extend(batch_embeddings)
        
        embedding_results = []
        for chunk, embedding in zip(chunks, all_embeddings):
            result = {
                "embedding": embedding,
                "text": chunk.text,
                "metadata": chunk.metadata,
                "chunk_id": chunk.chunk_id
            }
            embedding_results.append(result)
        
        if self.observability_service:
            self.observability_service.log_metrics("chunks_embedding_complete", {
                "total_chunks": len(chunks),
                "total_embeddings": len(embedding_results),
                "average_chunk_length": sum(len(chunk.text) for chunk in chunks) / len(chunks) if chunks else 0
            })
        
        return embedding_results 