import logging
import time
from contextlib import asynccontextmanager
from functools import wraps
from typing import Any, Dict, List, Optional
from langfuse import Langfuse, observe
from langfuse.openai import OpenAI
from app.core.config import Settings

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ObservabilityService:
    """Service for managing Langfuse observability and structured logging."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.langfuse_client = None
        self.instrumented_openai = None
        
        if settings.langfuse_secret_key and settings.langfuse_public_key:
            try:
                self.langfuse_client = Langfuse(
                    secret_key=settings.langfuse_secret_key,
                    public_key=settings.langfuse_public_key,
                    host=settings.langfuse_host
                )
                
                self.instrumented_openai = OpenAI(
                    api_key=settings.openai_api_key
                )
                
                logger.info("Langfuse observability initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Langfuse: {e}")
                self.langfuse_client = None
        else:
            logger.info("Langfuse keys not provided, observability disabled")
    
    @asynccontextmanager
    async def trace_operation(self, name: str, **kwargs):
        """Context manager for tracing operations with Langfuse."""
        start_time = time.time()
        
        logger.info(f"Starting operation: {name}", extra={
            "operation": name,
            "metadata": kwargs
        })
        
        span = None
        
        try:
            if self.langfuse_client:
                span = self.langfuse_client.start_span(
                    name=name,
                    metadata=kwargs,
                    input=kwargs
                )
            
            yield {
                "span": span,
                "start_time": start_time
            }
            
            duration = time.time() - start_time
            logger.info(f"Completed operation: {name}", extra={
                "operation": name,
                "duration_seconds": duration,
                "status": "success"
            })
            
            if span:
                span.update(output={"status": "success", "duration": duration})
                span.end()
                
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Failed operation: {name}", extra={
                "operation": name,
                "duration_seconds": duration,
                "status": "error",
                "error": str(e)
            })
            
            if span:
                span.update(output={"status": "error", "error": str(e), "duration": duration})
                span.end()
            
            raise
    
    def log_request(self, endpoint: str, payload: Dict[str, Any]):
        """Log incoming API requests."""
        logger.info(f"API Request: {endpoint}", extra={
            "endpoint": endpoint,
            "payload_size": len(str(payload)),
            "event_type": "api_request"
        })
    
    def log_response(self, endpoint: str, status_code: int, response_size: int):
        """Log API responses."""
        logger.info(f"API Response: {endpoint}", extra={
            "endpoint": endpoint,
            "status_code": status_code,
            "response_size": response_size,
            "event_type": "api_response"
        })
    
    def log_metrics(self, operation: str, metrics: Dict[str, Any]):
        """Log operation metrics."""
        logger.info(f"Metrics: {operation}", extra={
            "operation": operation,
            "metrics": metrics,
            "event_type": "metrics"
        })
    
    def get_instrumented_openai(self):
        """Get Langfuse-instrumented OpenAI client."""
        return self.instrumented_openai if self.instrumented_openai else None
    
    def create_generation(self, name: str, model: str, input_data: str, output_data: str, **kwargs):
        """Create a generation in Langfuse."""
        if self.langfuse_client:
            try:
                generation = self.langfuse_client.start_generation(
                    name=name,
                    model=model,
                    input=input_data,
                    metadata=kwargs
                )
                generation.update(output=output_data)
                generation.end()
            except Exception as e:
                logger.warning(f"Failed to create Langfuse generation: {e}")
    
    def flush(self):
        """Flush any pending Langfuse events."""
        if self.langfuse_client:
            try:
                self.langfuse_client.flush()
            except Exception as e:
                logger.warning(f"Failed to flush Langfuse events: {e}") 