from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional
import asyncio
import json
from app.models.schemas import (
    ChatRequest, ChatResponse, UploadResponse, 
    AnalyticsRequest, AnalyticsResponse
)
from app.services.pdf_processor import MultimodalPDFProcessor
from app.services.vector_store import MultimodalVectorStoreService
from langchain_server.graphs.rag_graph import MultimodalRAGGraph
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Global instances
pdf_processor = MultimodalPDFProcessor()
vector_service = MultimodalVectorStoreService()
rag_graph = MultimodalRAGGraph()

@router.post("/chat", response_model=ChatResponse)
async def chat_with_pdf(request: ChatRequest):
    """Main chat endpoint for PDF Q&A"""
    try:
        logger.info(f"Processing chat request: {request.query[:100]}...")
        
        # Process query through RAG graph
        result = await rag_graph.process_query(request.query)
        
        return ChatResponse(
            response=result["response"],
            chart_data=result.get("chart_data", {}),
            sources=result.get("sources", []),
            metadata=result.get("metadata", {}),
            query=request.query
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/stream")
async def chat_with_pdf_stream(request: ChatRequest):
    """Streaming chat endpoint"""
    try:
        async def generate_stream():
            # Process query through RAG graph
            result = await rag_graph.process_query(request.query)
            
            # Stream response word by word
            words = result["response"].split()
            for i, word in enumerate(words):
                chunk = {
                    "type": "text",
                    "content": word + " ",
                    "is_final": i == len(words) - 1
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                await asyncio.sleep(0.05)  # Small delay for streaming effect
            
            # Send chart data if available
            if result.get("chart_data"):
                chart_chunk = {
                    "type": "chart",
                    "content": result["chart_data"],
                    "is_final": True
                }
                yield f"data: {json.dumps(chart_chunk)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache"}
        )
        
    except Exception as e:
        logger.error(f"Error in streaming chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and process PDF file"""
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Save uploaded file
        import os
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"Processing uploaded PDF: {file.filename}")
        
        # Process PDF
        processed_content = await pdf_processor.process_pdf(file_path)
        
        # Add to vector stores
        await vector_service.add_multimodal_content(processed_content)
        
        return UploadResponse(
            message="PDF uploaded and processed successfully",
            filename=file.filename,
            page_count=processed_content["metadata"]["page_count"],
            text_chunks=len(processed_content["text_chunks"]),
            tables_found=len(processed_content["tables"]),
            images_found=len(processed_content["images"])
        )
        
    except Exception as e:
        logger.error(f"Error uploading PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analytics", response_model=AnalyticsResponse)
async def analyze_trends(request: AnalyticsRequest):
    """Advanced analytics endpoint for trend analysis"""
    try:
        # Search for relevant table data
        table_results = await vector_service.table_store.similarity_search(
            request.query, k=10
        )
        
        # Extract table data
        table_data = []
        for doc in table_results:
            if doc.metadata.get("content_type") == "table":
                # Get original table data
                table_data.extend(doc.metadata.get("table_data", []))
        
        if not table_data:
            return AnalyticsResponse(
                analysis="No relevant tabular data found for analysis.",
                insights=[],
                chart_data={},
                data_summary={}
            )
        
        # Generate analysis
        from app.services.llm_service import AdvancedLLMService
        llm_service = AdvancedLLMService()
        
        analysis_result = await llm_service.analyze_trends(
            request.query, table_data
        )
        
        # Generate chart if requested
        chart_data = {}
        if request.generate_chart:
            from app.utils.chart_generator import ChartGenerator
            chart_generator = ChartGenerator()
            chart_result = await chart_generator.generate_chart_from_query(
                request.query, table_results
            )
            chart_data = chart_result
        
        return AnalyticsResponse(
            analysis=analysis_result["analysis"],
            insights=analysis_result.get("insights", []),
            chart_data=chart_data,
            data_summary={
                "records_analyzed": len(table_data),
                "query": request.query
            }
        )
        
    except Exception as e:
        logger.error(f"Error in analytics endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "multimodal-pdf-rag"}