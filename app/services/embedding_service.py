from typing import List
import openai
from app.core.config import Settings
from app.utils.text_splitter import DocumentChunk


class EmbeddingService:
    
    def __init__(self, settings: Settings):
        self.settings = settings
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_embedding_model
    
    async def generate_embedding(self, text: str) -> List[float]:
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            raise RuntimeError(f"Failed to generate embedding: {str(e)}")
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            raise RuntimeError(f"Failed to generate batch embeddings: {str(e)}")
    
    async def embed_chunks(self, chunks: List[DocumentChunk]) -> List[dict]:
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
        
        return embedding_results 