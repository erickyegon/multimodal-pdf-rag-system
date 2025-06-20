from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import structlog
from typing import Dict, Any
import traceback

logger = structlog.get_logger()

class PDFProcessingError(Exception):
    """Custom exception for PDF processing errors"""
    def __init__(self, message: str, file_name: str = None, page_number: int = None):
        self.message = message
        self.file_name = file_name
        self.page_number = page_number
        super().__init__(self.message)

class VectorStoreError(Exception):
    """Custom exception for vector store operations"""
    def __init__(self, message: str, operation: str = None):
        self.message = message
        self.operation = operation
        super().__init__(self.message)

class LLMServiceError(Exception):
    """Custom exception for LLM service errors"""
    def __init__(self, message: str, model: str = None, tokens_used: int = None):
        self.message = message
        self.model = model
        self.tokens_used = tokens_used
        super().__init__(self.message)

async def pdf_processing_exception_handler(request: Request, exc: PDFProcessingError):
    """Handle PDF processing exceptions"""
    await logger.aerror(
        "pdf_processing_error",
        error_message=exc.message,
        file_name=exc.file_name,
        page_number=exc.page_number,
        traceback=traceback.format_exc()
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "PDF Processing Error",
            "message": exc.message,
            "details": {
                "file_name": exc.file_name,
                "page_number": exc.page_number
            }
        }
    )

async def vector_store_exception_handler(request: Request, exc: VectorStoreError):
    """Handle vector store exceptions"""
    await logger.aerror(
        "vector_store_error",
        error_message=exc.message,
        operation=exc.operation,
        traceback=traceback.format_exc()
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Vector Store Error",
            "message": exc.message,
            "operation": exc.operation
        }
    )

async def llm_service_exception_handler(request: Request, exc: LLMServiceError):
    """Handle LLM service exceptions"""
    await logger.aerror(
        "llm_service_error",
        error_message=exc.message,
        model=exc.model,
        tokens_used=exc.tokens_used,
        traceback=traceback.format_exc()
    )
    
    return JSONResponse(
        status_code=503,
        content={
            "error": "LLM Service Error",
            "message": exc.message,
            "model": exc.model
        }
    )

async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    await logger.aerror(
        "unexpected_error",
        error_type=type(exc).__name__,
        error_message=str(exc),
        request_path=str(request.url),
        request_method=request.method,
        traceback=traceback.format_exc()
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later."
        }
    )