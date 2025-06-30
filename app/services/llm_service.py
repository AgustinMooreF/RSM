from typing import List
import openai
from app.core.config import Settings


class LLMService:
    """Service for LLM-based question answering."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
    
    async def generate_answer(self, question: str, context_chunks: List[dict]) -> str:
        """Generate an answer based on question and context chunks."""
        try:
            context_texts = []
            for chunk in context_chunks:
                metadata = chunk.get("metadata", {})
                text = chunk.get("text", "")
                
                source_info = ""
                if metadata.get("page"):
                    source_info = f" (Page {metadata['page']})"
                elif metadata.get("filename"):
                    source_info = f" (Source: {metadata['filename']})"
                
                context_texts.append(f"{text}{source_info}")
            
            context = "\n\n".join(context_texts)
            
            prompt = f"""Based on the following context, please answer the question. If the answer cannot be found in the context, say "I don't have enough information to answer this question."

                    Context:
                    {context}

                    Question: {question}

                    Answer:"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions based on provided context. Be concise and accurate."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            return content.strip() if content else "I couldn't generate an answer."
        
        except Exception as e:
            raise RuntimeError(f"Failed to generate answer: {str(e)}") 