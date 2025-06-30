from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import uuid
import re


class DocumentChunk:
    """Represents a document chunk with metadata."""
    
    def __init__(self, text: str, metadata: dict, chunk_id: str = None):
        self.text = text
        self.metadata = metadata
        self.chunk_id = chunk_id or str(uuid.uuid4())


class SmartTextSplitter:
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n--- Page", "\n\n", "\n", " ", ""]
        )
    
    def _extract_page_number(self, text: str) -> int:
        page_match = re.search(r"--- Page (\d+) ---", text)
        if page_match:
            return int(page_match.group(1))
        return None
    
    def split_document(self, document: Document) -> List[DocumentChunk]:
        """Split a document into chunks with metadata preservation."""
        chunks = self.text_splitter.split_documents([document])
        
        document_chunks = []
        for i, chunk in enumerate(chunks):
            metadata = {
                **chunk.metadata,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "chunk_size": len(chunk.page_content),
                "original_length": len(document.page_content)
            }
            
            # Extract page number if this is a PDF chunk
            if chunk.metadata.get("type") == "pdf":
                page_num = self._extract_page_number(chunk.page_content)
                if page_num:
                    metadata["page"] = page_num
                    

                clean_text = re.sub(r"\n--- Page \d+ ---\n", "\n", chunk.page_content)
                chunk.page_content = clean_text.strip()
            
            document_chunk = DocumentChunk(
                text=chunk.page_content,
                metadata=metadata
            )
            document_chunks.append(document_chunk)
        
        return document_chunks 