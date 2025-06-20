from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
import asyncio
import logging
import time

from app.models.schemas import AnalyticsRequest, AnalyticsResponse, TrendAnalysisResult
from app.services.analytics_service import AnalyticsService
from app.services.vector_store import MultimodalVectorStoreService
from app.services.llm_service import AdvancedLLMService
from app.utils.chart_generator import ChartGenerator
from app.monitoring.prometheus import metrics_collector

logger = logging.getLogger(__name__)
router = APIRouter()

# Global services
analytics_service = AnalyticsService()
vector_service = MultimodalVectorStoreService()
llm_service = AdvancedLLMService()
chart_generator = ChartGenerator()

@router.post("/analytics", response_model=AnalyticsResponse)
async def run_analytics(request: AnalyticsRequest):
    """Run comprehensive analytics on document data"""
    start_time = time.time()
    
    try:
        logger.info(f"Running analytics for query: {request.query[:100]}...")
        
        # Search for relevant content
        search_results = await vector_service.search_multimodal(
            query=request.query,
            content_types=["text", "table", "image"],
            k_per_type=10
        )
        
        # Extract table data for analysis
        table_data = await analytics_service.extract_table_data(
            search_results.get("table", [])
        )
        
        # Generate analysis
        analysis_result = await analytics_service.analyze_data(
            query=request.query,
            table_data=table_data,
            context_docs=search_results.get("text", [])
        )
        
        # Generate insights
        insights = await analytics_service.extract_insights(
            analysis_result["analysis"],
            table_data
        )
        
        # Generate chart if requested
        chart_data = {}
        if request.generate_chart and table_data:
            chart_result = await chart_generator.generate_chart_from_query(
                query=request.query,
                table_docs=search_results.get("table", [])
            )
            chart_data = chart_result
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Record metrics
        metrics_collector.record_vector_search("analytics", response_time)
        
        return AnalyticsResponse(
            analysis=analysis_result["analysis"],
            insights=insights,
            chart_data=chart_data,
            data_summary={
                "records_analyzed": len(table_data),
                "query": request.query,
                "response_time": response_time,
                "sources_found": {
                    "text": len(search_results.get("text", [])),
                    "tables": len(search_results.get("table", [])),
                    "images": len(search_results.get("image", []))
                }
            },
            metadata={
                "analysis_type": analytics_service.classify_query_type(request.query),
                "confidence_score": analysis_result.get("confidence", 0.8)
            }
        )
        
    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Analytics processing failed: {str(e)}"
        )

@router.post("/trends")
async def analyze_trends(request: AnalyticsRequest):
    """Specialized endpoint for trend analysis"""
    try:
        # Force trend analysis
        trend_result = await analytics_service.analyze_trends(
            query=request.query,
            time_series_analysis=True
        )
        
        return TrendAnalysisResult(
            trends=trend_result["trends"],
            forecast=trend_result.get("forecast"),
            seasonality=trend_result.get("seasonality"),
            anomalies=trend_result.get("anomalies"),
            confidence=trend_result.get("confidence", 0.8)
        )
        
    except Exception as e:
        logger.error(f"Trend analysis error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Trend analysis failed: {str(e)}"
        )

@router.post("/compare")
async def compare_datasets(
    query: str,
    dataset_a: str,
    dataset_b: str
):
    """Compare two datasets or time periods"""
    try:
        comparison_result = await analytics_service.compare_datasets(
            query=query,
            dataset_a_query=dataset_a,
            dataset_b_query=dataset_b
        )
        
        return comparison_result
        
    except Exception as e:
        logger.error(f"Dataset comparison error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Dataset comparison failed: {str(e)}"
        )

@router.get("/metrics/{document_id}")
async def get_document_metrics(document_id: str):
    """Get comprehensive metrics for a document"""
    try:
        metrics = await analytics_service.get_document_metrics(document_id)
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting document metrics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get document metrics: {str(e)}"
        )

@router.post("/export")
async def export_analytics(
    query: str,
    format: str = "json",
    include_charts: bool = True
):
    """Export analytics results in various formats"""
    try:
        export_result = await analytics_service.export_analysis(
            query=query,
            format=format,
            include_charts=include_charts
        )
        
        return export_result
        
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Export failed: {str(e)}"
        )