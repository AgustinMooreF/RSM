from app.core.config import Settings
from app.models.schemas import IngestResponse, QueryResponse, Source
from app.utils.document_loader import DocumentLoader
from app.utils.text_splitter import SmartTextSplitter
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from app.services.llm_service import LLMService


class DocumentService:
    """Main service for document processing with comprehensive Langfuse observability."""
    
    def __init__(self, settings: Settings, observability_service=None):
        self.settings = settings
        self.observability_service = observability_service
        
        # Initialize all services with observability
        self.document_loader = DocumentLoader()
        self.text_splitter = SmartTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        self.embedding_service = EmbeddingService(settings, observability_service)
        self.vector_service = VectorService(settings, observability_service)
        self.llm_service = LLMService(settings, observability_service)
    
    async def ingest_document(self, content: str, document_type: str) -> IngestResponse:
        """Ingest a document from text content or URL with full observability."""
        if self.observability_service:
            async with self.observability_service.trace_operation(
                "document_ingestion",
                document_type=document_type,
                content_length=len(content)
            ):
                return await self._ingest_document_impl(content, document_type)
        else:
            return await self._ingest_document_impl(content, document_type)
    
    async def _ingest_document_impl(self, content: str, document_type: str) -> IngestResponse:
        """Internal implementation of document ingestion."""
        try:
            if self.observability_service:
                async with self.observability_service.trace_operation(
                    "document_loading_and_chunking",
                    document_type=document_type,
                    content_length=len(content)
                ):
                    document = self.document_loader.load_document(content, document_type)
                    chunks = self.text_splitter.split_document(document)
            else:
                document = self.document_loader.load_document(content, document_type)
                chunks = self.text_splitter.split_document(document)
            
            if not chunks:
                return IngestResponse(
                    status="error",
                    message="No chunks were created from the document",
                    chunks_created=0,
                    document_info=None
                )
            
            if self.observability_service:
                self.observability_service.log_metrics("document_chunking", {
                    "original_length": len(document.page_content),
                    "chunks_created": len(chunks),
                    "average_chunk_size": sum(len(chunk.text) for chunk in chunks) / len(chunks) if chunks else 0,
                    "document_type": document_type
                })
            
            embedding_results = await self.embedding_service.embed_chunks(chunks)
            
            stored_count = await self.vector_service.store_embeddings(embedding_results)
            
            document_info = {
                "source": document.metadata.get("source", "direct_input"),
                "type": document.metadata.get("type"),
                "total_pages": document.metadata.get("total_pages"),
                "original_length": len(document.page_content)
            }
            
            # Log final ingestion metrics
            if self.observability_service:
                self.observability_service.log_metrics("document_ingestion_complete", {
                    "chunks_created": stored_count,
                    "document_type": document_type,
                    "success": True
                })
            
            return IngestResponse(
                status="success",
                message=f"Successfully ingested document with {stored_count} chunks",
                chunks_created=stored_count,
                document_info=document_info
            )
        
        except Exception as e:
            if self.observability_service:
                self.observability_service.log_metrics("document_ingestion_error", {
                    "error": str(e),
                    "document_type": document_type,
                    "success": False
                })
            
            return IngestResponse(
                status="error",
                message=f"Failed to ingest document: {str(e)}",
                chunks_created=0,
                document_info=None
            )
    
    async def ingest_file(self, file_content: bytes, filename: str, document_type: str) -> IngestResponse:
        """Ingest a document from uploaded file with observability."""
        if self.observability_service:
            async with self.observability_service.trace_operation(
                "file_ingestion",
                filename=filename,
                document_type=document_type,
                file_size=len(file_content)
            ):
                return await self._ingest_file_impl(file_content, filename, document_type)
        else:
            return await self._ingest_file_impl(file_content, filename, document_type)
    
    async def _ingest_file_impl(self, file_content: bytes, filename: str, document_type: str) -> IngestResponse:
        """Internal implementation of file ingestion."""
        try:
            metadata = {
                "filename": filename,
                "type": document_type,
                "source_type": "file_upload"
            }
            
            if self.observability_service:
                async with self.observability_service.trace_operation(
                    "file_processing_and_chunking",
                    filename=filename,
                    document_type=document_type,
                    file_size=len(file_content)
                ):
                    if document_type == "pdf":
                        document = self.document_loader.load_pdf(file_content, metadata)
                    else:
                        raise ValueError(f"type: {document_type} not supported")
                    
                    chunks = self.text_splitter.split_document(document)
            else:
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
            
            if self.observability_service:
                self.observability_service.log_metrics("file_processing", {
                    "filename": filename,
                    "file_size": len(file_content),
                    "chunks_created": len(chunks),
                    "document_type": document_type,
                    "total_pages": document.metadata.get("total_pages", 0)
                })
            
            embedding_results = await self.embedding_service.embed_chunks(chunks)
            stored_count = await self.vector_service.store_embeddings(embedding_results)
            
            document_info = {
                "filename": filename,
                "type": document.metadata.get("type"),
                "total_pages": document.metadata.get("total_pages"),
                "original_length": len(document.page_content),
                "file_size_bytes": len(file_content)
            }
            
            if self.observability_service:
                self.observability_service.log_metrics("file_ingestion_complete", {
                    "filename": filename,
                    "chunks_stored": stored_count,
                    "success": True
                })
            
            return IngestResponse(
                status="success",
                message=f"Successfully ingested file '{filename}' with {stored_count} chunks",
                chunks_created=stored_count,
                document_info=document_info
            )
        
        except Exception as e:
            # Log error metrics
            if self.observability_service:
                self.observability_service.log_metrics("file_ingestion_error", {
                    "filename": filename,
                    "error": str(e),
                    "success": False
                })
            
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
        """Query documents using RAG with comprehensive observability."""
        if self.observability_service:
            async with self.observability_service.trace_operation(
                "rag_query",
                question=question,
                question_length=len(question)
            ):
                return await self._query_documents_impl(question)
        else:
            return await self._query_documents_impl(question)
    
    async def _query_documents_impl(self, question: str) -> QueryResponse:
        """Internal implementation of RAG query."""
        try:
            # Generate question embedding
            question_embedding = await self.embedding_service.generate_embedding(question)
            
            # Search for similar chunks
            similar_chunks = await self.vector_service.search_similar(
                query_embedding=question_embedding,
                top_k=5
            )
            
            if not similar_chunks:
                return QueryResponse(
                    answer="I don't have any relevant documents to answer this question.",
                    sources=[]
                )
            
            # Log retrieval metrics
            if self.observability_service:
                self.observability_service.log_metrics("rag_retrieval", {
                    "question_length": len(question),
                    "chunks_retrieved": len(similar_chunks),
                    "average_similarity": sum(1 - chunk.get("distance", 1) for chunk in similar_chunks) / len(similar_chunks) if similar_chunks else 0
                })
            
            # Generate answer using LLM
            answer = await self.llm_service.generate_answer(question, similar_chunks)
            
            # Prepare sources
            sources = []
            for chunk in similar_chunks:
                metadata = chunk.get("metadata", {})
                source = Source(
                    page=metadata.get("page"),
                    text=chunk.get("text", "")[:200] + "..." if len(chunk.get("text", "")) > 200 else chunk.get("text", "")
                )
                sources.append(source)
            
            # Log final query metrics
            if self.observability_service:
                self.observability_service.log_metrics("rag_query_complete", {
                    "question_length": len(question),
                    "answer_length": len(answer),
                    "sources_returned": len(sources),
                    "success": True
                })
            
            return QueryResponse(
                answer=answer,
                sources=sources
            )
        
        except Exception as e:
            # Log error metrics
            if self.observability_service:
                self.observability_service.log_metrics("rag_query_error", {
                    "question": question,
                    "error": str(e),
                    "success": False
                })
            
            return QueryResponse(
                answer=f"An error occurred while processing your question: {str(e)}",
                sources=[]
            ) 