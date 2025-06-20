from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sys
import os
import time
import asyncio

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.logging import setup_logging, RequestLoggingMiddleware
from app.core.exceptions import (
    PDFProcessingError, VectorStoreError, LLMServiceError,
    pdf_processing_exception_handler, vector_store_exception_handler,
    llm_service_exception_handler, general_exception_handler
)
from app.api.routes import chat, upload, analytics, health
from app.services.vector_store import MultimodalVectorStoreService
from app.services.database import db_service
from app.monitoring.prometheus import metrics_collector

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    
    # Initialize services
    try:
        # Initialize database
        logger.info("Initializing database...")
        # Database tables are created automatically in db_service.__init__
        
        # Initialize vector store
        logger.info("Initializing vector store...")
        vector_service = MultimodalVectorStoreService()
        
        # Create necessary directories
        settings.get_upload_path()
        settings.get_processed_path()
        settings.get_chroma_path()
        
        # Health check for external services
        if settings.EURI_API_KEY:
            logger.info("EURI AI configuration detected")
        else:
            logger.warning("EURI_API_KEY not configured")
        
        logger.info("✅ All services initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Error during startup: {str(e)}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down services...")

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(RequestLoggingMiddleware)

# Add exception handlers
app.add_exception_handler(PDFProcessingError, pdf_processing_exception_handler)
app.add_exception_handler(VectorStoreError, vector_store_exception_handler)
app.add_exception_handler(LLMServiceError, llm_service_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Basic rate limiting middleware"""
    start_time = time.time()
    
    # Skip rate limiting for health checks
    if request.url.path in ["/health", "/health/live", "/health/ready"]:
        response = await call_next(request)
        return response
    
    # TODO: Implement proper rate limiting with Redis
    # For now, just add processing time header
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# Include routers
app.include_router(
    chat.router,
    prefix=f"{settings.API_V1_STR}/chat",
    tags=["chat"]
)

app.include_router(
    upload.router,
    prefix=f"{settings.API_V1_STR}/upload",
    tags=["upload"]
)

app.include_router(
    analytics.router,
    prefix=f"{settings.API_V1_STR}/analytics",
    tags=["analytics"]
)

app.include_router(
    health.router,
    prefix="/health",
    tags=["health"]
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "status": "running",
        "docs": "/docs" if settings.DEBUG else "disabled",
        "api": settings.API_V1_STR
    }

@app.get("/info")
async def get_system_info():
    """Get system information"""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": settings.DESCRIPTION,
        "environment": "development" if settings.DEBUG else "production",
        "features": {
            "multimodal_processing": True,
            "analytics": settings.ENABLE_ANALYTICS,
            "metrics": settings.ENABLE_METRICS,
            "vector_db": settings.VECTOR_DB_TYPE
        },
        "limits": {
            "max_file_size": settings.MAX_FILE_SIZE,
            "max_query_length": settings.MAX_QUERY_LENGTH,
            "supported_formats": settings.ALLOWED_FILE_TYPES
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )