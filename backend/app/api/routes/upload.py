from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import os
import asyncio
import logging
from datetime import datetime
import uuid

from app.core.config import settings
from app.services.pdf_processor import MultimodalPDFProcessor
from app.services.vector_store import MultimodalVectorStoreService
from app.services.database import db_service
from app.models.schemas import UploadResponse, DocumentInfo, ProcessingStatus
from app.core.exceptions import PDFProcessingError
from app.monitoring.prometheus import metrics_collector

logger = logging.getLogger(__name__)
router = APIRouter()

# Global services
pdf_processor = MultimodalPDFProcessor()
vector_service = MultimodalVectorStoreService()

@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Upload and process PDF file"""
    
    # Validate file
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400, 
            detail="Only PDF files are allowed"
        )
    
    if file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB"
        )
    
    # Generate unique file ID
    file_id = str(uuid.uuid4())
    
    try:
        # Create upload directory if it doesn't exist
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        # Save file with unique name
        file_extension = os.path.splitext(file.filename)[1]
        saved_filename = f"{file_id}{file_extension}"
        file_path = os.path.join(settings.UPLOAD_DIR, saved_filename)
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"File uploaded: {file.filename} -> {saved_filename}")
        
        # Create document record in database
        document_data = {
            "id": file_id,
            "filename": saved_filename,
            "original_filename": file.filename,
            "file_path": file_path,
            "file_size": len(content),
            "processing_status": "pending"
        }
        
        document = await db_service.create_document(document_data)
        
        # Start background processing
        background_tasks.add_task(
            process_pdf_background,
            file_id,
            file_path,
            file.filename
        )
        
        return UploadResponse(
            document_id=file_id,
            message=f"File '{file.filename}' uploaded successfully. Processing started.",
            filename=file.filename,
            file_size=len(content),
            status="processing"
        )
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        
        # Clean up file if it was saved
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
            
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file: {str(e)}"
        )

async def process_pdf_background(document_id: str, file_path: str, original_filename: str):
    """Background task to process PDF"""
    start_time = datetime.utcnow()
    
    try:
        # Update status to processing
        await db_service.update_document_status(document_id, "processing")
        
        logger.info(f"Starting PDF processing for: {original_filename}")
        
        # Process PDF
        processed_content = await pdf_processor.process_pdf(file_path)
        
        # Add to vector stores
        await vector_service.add_multimodal_content(processed_content)
        
        # Calculate processing metrics
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        page_count = processed_content["metadata"]["page_count"]
        file_size = os.path.getsize(file_path)
        
        # Update document with processing results
        metadata = {
            "page_count": page_count,
            "text_chunks": len(processed_content["text_chunks"]),
            "tables_found": len(processed_content["tables"]),
            "images_found": len(processed_content["images"]),
            "processing_time": processing_time
        }
        
        await db_service.update_document_status(
            document_id, 
            "completed", 
            metadata
        )
        
        # Record metrics
        metrics_collector.record_pdf_processing(file_size, processing_time)
        
        logger.info(f"PDF processing completed for: {original_filename}")
        
    except Exception as e:
        logger.error(f"PDF processing failed for {original_filename}: {str(e)}")
        
        await db_service.update_document_status(
            document_id, 
            "failed", 
            {"error": str(e)}
        )

@router.get("/documents", response_model=List[DocumentInfo])
async def list_documents():
    """List all uploaded documents"""
    try:
        documents = await db_service.list_documents()
        
        return [
            DocumentInfo(
                id=doc.id,
                filename=doc.original_filename,
                upload_date=doc.upload_date,
                file_size=doc.file_size,
                page_count=doc.processing_metadata.get("page_count", 0) if doc.processing_metadata else 0,
                status=doc.processing_status,
                text_chunks=doc.processing_metadata.get("text_chunks", 0) if doc.processing_metadata else 0,
                tables_found=doc.processing_metadata.get("tables_found", 0) if doc.processing_metadata else 0,
                images_found=doc.processing_metadata.get("images_found", 0) if doc.processing_metadata else 0
            )
            for doc in documents
        ]
        
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list documents")

@router.get("/documents/{document_id}/status", response_model=ProcessingStatus)
async def get_document_status(document_id: str):
    """Get processing status of a document"""
    try:
        document = await db_service.get_document(document_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return ProcessingStatus(
            document_id=document_id,
            status=document.processing_status,
            progress=100 if document.processing_status == "completed" else 
                    50 if document.processing_status == "processing" else 0,
            message=f"Document is {document.processing_status}",
            metadata=document.processing_metadata or {}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get document status")

@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and its processed data"""
    try:
        document = await db_service.get_document(document_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete file from filesystem
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # TODO: Remove from vector stores
        # This would require implementing document-specific removal in vector stores
        
        # Delete from database
        await db_service.delete_document(document_id)
        
        logger.info(f"Document deleted: {document.original_filename}")
        
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete document")

@router.get("/documents/{document_id}/analytics")
async def get_document_analytics(document_id: str):
    """Get analytics for a specific document"""
    try:
        analytics = await db_service.get_document_analytics(document_id)
        
        if not analytics:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get document analytics")