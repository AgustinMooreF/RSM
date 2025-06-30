import requests
import io
from typing import Dict, Any, Union, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
import pdfplumber


class DocumentLoader:
    """Utility class for loading documents of different types."""
    
    @staticmethod
    def load_text(content: str, metadata: Optional[Dict[str, Any]] = None) -> Document:
        if metadata is None:
            metadata = {"type": "text"}
        return Document(page_content=content, metadata=metadata)
    
    @staticmethod
    def load_html(content: str, metadata: Optional[Dict[str, Any]] = None) -> Document:
        soup = BeautifulSoup(content, 'html.parser')
        
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text()
        
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        if metadata is None:
            metadata = {"type": "html"}
        
        return Document(page_content=text, metadata=metadata)
    
    @staticmethod
    def load_markdown(content: str, metadata: Optional[Dict[str, Any]] = None) -> Document:
        if metadata is None:
            metadata = {"type": "markdown"}
        return Document(page_content=content, metadata=metadata)
    
    @staticmethod
    def load_pdf(content: Union[str, bytes], metadata: Optional[Dict[str, Any]] = None) -> Document:
        if metadata is None:
            metadata = {"type": "pdf"}
        
        try:
            if isinstance(content, str):
                with pdfplumber.open(content) as pdf:
                    text_parts = []
                    total_pages = len(pdf.pages)
                    
                    for page_num, page in enumerate(pdf.pages, 1):
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(f"\n--- Page {page_num} ---\n{page_text}")
                    
                    full_text = "\n".join(text_parts)
                    
                    metadata.update({
                        "total_pages": total_pages,
                        "source_type": "pdf_file"
                    })
            
            elif isinstance(content, bytes):
                with pdfplumber.open(io.BytesIO(content)) as pdf:
                    text_parts = []
                    total_pages = len(pdf.pages)
                    
                    for page_num, page in enumerate(pdf.pages, 1):
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(f"\n--- Page {page_num} ---\n{page_text}")
                    
                    full_text = "\n".join(text_parts)
                    
                    metadata.update({
                        "total_pages": total_pages,
                        "source_type": "pdf_bytes"
                    })
            
            else:
                raise ValueError("PDF content must be either a file path (str) or binary data (bytes)")
            
            if not full_text.strip():
                raise ValueError("No text could be extracted from the PDF")
            
            return Document(page_content=full_text, metadata=metadata)
        
        except Exception as e:
            raise ValueError(f"Failed to process PDF: {str(e)}")
    
    @staticmethod
    def load_pdf_from_url(url: str) -> Document:
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            metadata = {
                "source": url,
                "type": "pdf"
            }
            
            return DocumentLoader.load_pdf(response.content, metadata)
            
        except requests.RequestException as e:
            raise ValueError(f"Failed to download PDF from URL {url}: {str(e)}")
    
    @staticmethod
    def load_from_url(url: str, document_type: str = "html") -> Document:
        try:
            if document_type == "pdf":
                return DocumentLoader.load_pdf_from_url(url)
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            metadata = {
                "source": url,
                "type": document_type
            }
            
            if document_type == "html":
                return DocumentLoader.load_html(response.text, metadata)
            else:
                return DocumentLoader.load_text(response.text, metadata)
                
        except requests.RequestException as e:
            raise ValueError(f"Failed to load document from URL {url}: {str(e)}")
    
    @classmethod
    def load_document(cls, content: str, document_type: str) -> Document:
        if content.startswith(("http://", "https://")):
            return cls.load_from_url(content, document_type)
        
        if document_type == "html":
            return cls.load_html(content)
        elif document_type == "markdown":
            return cls.load_markdown(content)
        elif document_type == "text":
            return cls.load_text(content)
        elif document_type == "pdf":
            # For PDF, assume content is a file path
            return cls.load_pdf(content)
        else:
            raise ValueError(f"Unsupported document type: {document_type}") 