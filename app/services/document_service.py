from app.core.config import Settings
from app.models.schemas import IngestResponse, QueryResponse, Source
from app.utils.document_loader import DocumentLoader
from app.utils.text_splitter import SmartTextSplitter
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from app.services.llm_service import LLMService


class DocumentService:
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.document_loader = DocumentLoader()
        self.text_splitter = SmartTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        self.embedding_service = EmbeddingService(settings)
        self.vector_service = VectorService(settings)
        self.llm_service = LLMService(settings)
    
    async def ingest_document(self, content: str, document_type: str) -> IngestResponse:
        """Ingest a document from text content or URL."""
        try:
            document = self.document_loader.load_document(content, document_type)
            
            chunks = self.text_splitter.split_document(document)
            
            if not chunks:
                return IngestResponse(
                    status="error",
                    message="No chunks were created from the document",
                    chunks_created=0,
                    document_info=None
                )
            
            embedding_results = await self.embedding_service.embed_chunks(chunks)
            
            stored_count = await self.vector_service.store_embeddings(embedding_results)
            
            document_info = {
                "source": document.metadata.get("source", "direct_input"),
                "type": document.metadata.get("type"),
                "total_pages": document.metadata.get("total_pages"),
                "original_length": len(document.page_content)
            }
            
            return IngestResponse(
                status="success",
                message=f"Successfully ingested document with {stored_count} chunks",
                chunks_created=stored_count,
                document_info=document_info
            )
        
        except Exception as e:
            return IngestResponse(
                status="error",
                message=f"Failed to ingest document: {str(e)}",
                chunks_created=0,
                document_info=None
            )
    
    async def ingest_file(self, file_content: bytes, filename: str, document_type: str) -> IngestResponse:
        """Ingest a document from uploaded file."""
        try:
            metadata = {
                "filename": filename,
                "type": document_type,
                "source_type": "file_upload"
            }
            
            if document_type == "pdf":
                document = self.document_loader.load_pdf(file_content, metadata)
            else:
                raise ValueError(f"type: {document_type} not supported")
            
            chunks = self.text_splitter.split_document(document)
            
            if not chunks:
                return IngestResponse(
                    status="error",
                    message="No chunks were created",
                    chunks_created=0,
                    document_info=None
                )
            
            embedding_results = await self.embedding_service.embed_chunks(chunks)
            stored_count = await self.vector_service.store_embeddings(embedding_results)
            
            document_info = {
                "filename": filename,
                "type": document.metadata.get("type"),
                "total_pages": document.metadata.get("total_pages"),
                "original_length": len(document.page_content),
                "file_size_bytes": len(file_content)
            }
            
            return IngestResponse(
                status="success",
                message=f"Successfully ingested file '{filename}' with {stored_count} chunks",
                chunks_created=stored_count,
                document_info=document_info
            )
        
        except Exception as e:
            return IngestResponse(
                status="error",
                message=f"Failed to ingest file '{filename}': {str(e)}",
                chunks_created=0,
                document_info=None
            )
    
    async def get_stats(self) -> dict:
        """Get statistics about the document store."""
        return await self.vector_service.get_collection_stats()
    
    async def query_documents(self, question: str) -> QueryResponse:
        """Query documents using RAG (Retrieval-Augmented Generation)."""
        try:
            question_embedding = await self.embedding_service.generate_embedding(question)
            
            similar_chunks = await self.vector_service.search_similar(
                query_embedding=question_embedding,
                top_k=5
            )
            
            if not similar_chunks:
                return QueryResponse(
                    answer="I don't have any relevant documents to answer this question.",
                    sources=[]
                )
            
            answer = await self.llm_service.generate_answer(question, similar_chunks)
            

            sources = []
            for chunk in similar_chunks:
                metadata = chunk.get("metadata", {})
                source = Source(
                    page=metadata.get("page"),
                    text=chunk.get("text", "")[:200] + "..." if len(chunk.get("text", "")) > 200 else chunk.get("text", "")
                )
                sources.append(source)
            
            return QueryResponse(
                answer=answer,
                sources=sources
            )
        
        except Exception as e:
            return QueryResponse(
                answer=f"An error occurred while processing your question: {str(e)}",
                sources=[]
            ) 