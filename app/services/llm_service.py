from typing import List
import openai
from app.core.config import Settings


class LLMService:
    """Service for LLM-based question answering with Langfuse observability."""
    
    def __init__(self, settings: Settings, observability_service=None):
        self.settings = settings
        self.observability_service = observability_service
        
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key is required")
        
        if observability_service and observability_service.get_instrumented_openai():
            self.client = observability_service.get_instrumented_openai()
        else:
            self.client = openai.OpenAI(api_key=settings.openai_api_key)
        
        self.model = settings.openai_model
    
    async def generate_answer(self, question: str, context_chunks: List[dict]) -> str:
        """Generate an answer based on question and context chunks with observability."""
        
        if self.observability_service:
            async with self.observability_service.trace_operation(
                "llm_generation",
                model=self.model,
                question=question,
                context_count=len(context_chunks)
            ) as trace_context:
                return await self._generate_answer_impl(question, context_chunks, trace_context)
        else:
            return await self._generate_answer_impl(question, context_chunks, None)
    
    async def _generate_answer_impl(self, question: str, context_chunks: List[dict], trace_context=None) -> str:
        """Internal implementation of answer generation."""
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
            
            if self.observability_service:
                self.observability_service.log_metrics("llm_generation", {
                    "context_length": len(context),
                    "context_chunks": len(context_chunks),
                    "question_length": len(question),
                    "model": self.model
                })
            
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
            answer = content.strip() if content else "I couldn't generate an answer."
            
            if self.observability_service and hasattr(response, 'usage') and response.usage:
                self.observability_service.log_metrics("llm_usage", {
                    "prompt_tokens": getattr(response.usage, 'prompt_tokens', 0),
                    "completion_tokens": getattr(response.usage, 'completion_tokens', 0),
                    "total_tokens": getattr(response.usage, 'total_tokens', 0)
                })
            
            return answer
            
        except Exception as e:
            raise RuntimeError(f"Failed to generate answer: {str(e)}") 