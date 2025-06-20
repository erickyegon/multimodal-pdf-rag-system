import structlog
import logging
import sys
from datetime import datetime
from app.core.config import settings
from typing import Dict, Any

def setup_logging():
    """Configure structured logging"""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.JSONRenderer() if settings.LOG_LEVEL == "PRODUCTION" 
            else structlog.dev.ConsoleRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    )

class RequestLoggingMiddleware:
    """Middleware for logging HTTP requests"""
    
    def __init__(self, app):
        self.app = app
        self.logger = structlog.get_logger()
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = datetime.utcnow()
        
        # Log request
        await self.logger.ainfo(
            "request_started",
            method=scope["method"],
            path=scope["path"],
            query_string=scope["query_string"].decode(),
            client_ip=scope.get("client", ["unknown"])[0]
        )
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Calculate response time
                response_time = (datetime.utcnow() - start_time).total_seconds()
                
                await self.logger.ainfo(
                    "request_completed",
                    method=scope["method"],
                    path=scope["path"],
                    status_code=message["status"],
                    response_time_ms=round(response_time * 1000, 2)
                )
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)

class ApplicationMetrics:
    """Application metrics collector"""
    
    def __init__(self):
        self.logger = structlog.get_logger()
        self._metrics = {}
    
    async def record_pdf_processing(self, file_size: int, page_count: int, processing_time: float):
        """Record PDF processing metrics"""
        await self.logger.ainfo(
            "pdf_processing_completed",
            file_size_mb=round(file_size / (1024 * 1024), 2),
            page_count=page_count,
            processing_time_seconds=round(processing_time, 2),
            pages_per_second=round(page_count / processing_time, 2) if processing_time > 0 else 0
        )
    
    async def record_query_response(self, query: str, response_time: float, tokens_used: int = None):
        """Record chat query metrics"""
        await self.logger.ainfo(
            "query_processed",
            query_length=len(query),
            response_time_seconds=round(response_time, 2),
            tokens_used=tokens_used
        )
    
    async def record_vector_search(self, query: str, results_count: int, search_time: float):
        """Record vector search metrics"""
        await self.logger.ainfo(
            "vector_search_completed",
            query_length=len(query),
            results_count=results_count,
            search_time_ms=round(search_time * 1000, 2)
        )

# Global metrics instance
app_metrics = ApplicationMetrics()