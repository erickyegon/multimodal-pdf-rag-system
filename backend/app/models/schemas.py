from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum

# Existing schemas plus new ones for the additional functionality

class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class AnalysisType(str, Enum):
    GENERAL = "general"
    TREND = "trend_analysis"
    COMPARISON = "comparison"
    SUMMARY = "summary"
    PREDICTION = "prediction"

class ContentType(str, Enum):
    TEXT = "text"
    TABLE = "table"
    IMAGE = "image"

# Enhanced existing schemas
class ChatRequest(BaseModel):
    query: str = Field(..., description="User query about the PDF", min_length=1, max_length=2000)
    context_type: Optional[List[ContentType]] = Field(
        default=[ContentType.TEXT, ContentType.TABLE, ContentType.IMAGE],
        description="Types of content to search"
    )
    include_charts: bool = Field(
        default=True,
        description="Whether to generate charts for data queries"
    )
    document_id: Optional[str] = Field(
        default=None,
        description="Specific document to query (optional)"
    )

class ChatResponse(BaseModel):
    response: str = Field(..., description="Generated response")
    chart_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Chart data if applicable"
    )
    sources: List[str] = Field(
        default_factory=list,
        description="Source pages and content types"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    query: str = Field(..., description="Original query")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    processing_time: Optional[float] = Field(default=None, description="Response time in seconds")
    timestamp: datetime = Field(default_factory=datetime.now)

class UploadResponse(BaseModel):
    document_id: str = Field(..., description="Unique document identifier")
    message: str = Field(..., description="Upload status message")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    status: DocumentStatus = Field(..., description="Processing status")
    upload_timestamp: datetime = Field(default_factory=datetime.now)

class DocumentInfo(BaseModel):
    id: str = Field(..., description="Document ID")
    filename: str = Field(..., description="Original filename")
    upload_date: datetime = Field(..., description="Upload timestamp")
    file_size: int = Field(..., description="File size in bytes")
    page_count: int = Field(default=0, description="Number of pages")
    status: DocumentStatus = Field(..., description="Processing status")
    text_chunks: int = Field(default=0, description="Number of text chunks")
    tables_found: int = Field(default=0, description="Number of tables found")
    images_found: int = Field(default=0, description="Number of images found")

class ProcessingStatus(BaseModel):
    document_id: str = Field(..., description="Document ID")
    status: DocumentStatus = Field(..., description="Current status")
    progress: float = Field(..., ge=0.0, le=100.0, description="Progress percentage")
    message: str = Field(..., description="Status message")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")
    current_step: Optional[str] = Field(default=None, description="Current processing step")
    error_details: Optional[str] = Field(default=None, description="Error details if failed")

class AnalyticsRequest(BaseModel):
    query: str = Field(..., description="Analytics query", min_length=1, max_length=2000)
    generate_chart: bool = Field(
        default=True,
        description="Whether to generate visualization"
    )
    chart_type: Optional[str] = Field(
        default=None,
        description="Specific chart type if desired"
    )
    analysis_type: Optional[AnalysisType] = Field(
        default=AnalysisType.GENERAL,
        description="Type of analysis to perform"
    )
    document_id: Optional[str] = Field(
        default=None,
        description="Specific document to analyze"
    )
    include_recommendations: bool = Field(
        default=True,
        description="Whether to include actionable recommendations"
    )

class AnalyticsResponse(BaseModel):
    analysis: str = Field(..., description="Generated analysis")
    insights: List[str] = Field(
        default_factory=list,
        description="Key insights extracted"
    )
    chart_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Chart configuration and data"
    )
    data_summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Summary of analyzed data"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Actionable recommendations"
    )
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Confidence score")
    analysis_type: AnalysisType = Field(..., description="Type of analysis performed")
    processing_time: Optional[float] = Field(default=None, description="Analysis time in seconds")

class TrendAnalysisResult(BaseModel):
    trends: List[Dict[str, Any]] = Field(..., description="Identified trends")
    forecast: Optional[Dict[str, Any]] = Field(default=None, description="Forecast data")
    seasonality: Optional[Dict[str, Any]] = Field(default=None, description="Seasonal patterns")
    anomalies: List[Dict[str, Any]] = Field(default_factory=list, description="Detected anomalies")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Analysis confidence")
    time_period: Optional[str] = Field(default=None, description="Time period analyzed")

class ComparisonResult(BaseModel):
    comparison: str = Field(..., description="Comparison analysis")
    metrics: Dict[str, Any] = Field(..., description="Comparison metrics")
    winner: Optional[str] = Field(default=None, description="Best performing item")
    differences: List[Dict[str, Any]] = Field(..., description="Key differences")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)

class ExportRequest(BaseModel):
    query: str = Field(..., description="Analysis query to export")
    format: str = Field(default="json", description="Export format")
    include_charts: bool = Field(default=True, description="Include visualizations")
    include_raw_data: bool = Field(default=False, description="Include raw data")

class HealthCheckResponse(BaseModel):
    status: str = Field(..., description="Overall health status")
    components: Dict[str, Dict[str, Any]] = Field(..., description="Component health details")
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str = Field(default="1.0.0", description="System version")

class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = Field(default=None, description="Request identifier")

class UserSession(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    user_id: Optional[str] = Field(default=None, description="User identifier")
    document_id: Optional[str] = Field(default=None, description="Current document")
    created_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)
    query_count: int = Field(default=0, description="Number of queries in session")

class QueryMetrics(BaseModel):
    query: str = Field(..., description="User query")
    response_time: float = Field(..., description="Response time in seconds")
    tokens_used: Optional[int] = Field(default=None, description="LLM tokens consumed")
    sources_found: int = Field(..., description="Number of sources found")
    confidence: float = Field(..., description="Response confidence")
    timestamp: datetime = Field(default_factory=datetime.now)

class SystemMetrics(BaseModel):
    active_sessions: int = Field(..., description="Current active sessions")
    total_documents: int = Field(..., description="Total documents processed")
    total_queries: int = Field(..., description="Total queries processed")
    average_response_time: float = Field(..., description="Average response time")
    system_uptime: float = Field(..., description="System uptime in hours")
    memory_usage: float = Field(..., description="Memory usage percentage")
    cpu_usage: float = Field(..., description="CPU usage percentage")

# Validation helpers
class DocumentValidator:
    @staticmethod
    def validate_file_type(filename: str) -> bool:
        """Validate file type is PDF"""
        return filename.lower().endswith('.pdf')
    
    @staticmethod
    def validate_file_size(size: int, max_size: int = 104857600) -> bool:  # 100MB default
        """Validate file size"""
        return 0 < size <= max_size

class QueryValidator:
    @staticmethod
    def validate_query_length(query: str, max_length: int = 2000) -> bool:
        """Validate query length"""
        return 1 <= len(query.strip()) <= max_length
    
    @staticmethod
    def validate_query_safety(query: str) -> bool:
        """Basic safety validation for queries"""
        dangerous_patterns = [
            "exec", "eval", "import", "open", "file", "__", 
            "system", "subprocess", "os.", "shell"
        ]
        query_lower = query.lower()
        return not any(pattern in query_lower for pattern in dangerous_patterns)