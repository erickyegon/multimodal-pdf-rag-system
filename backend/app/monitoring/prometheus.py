from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time
from functools import wraps

# Metrics definitions
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

PDF_PROCESSING_DURATION = Histogram(
    'pdf_processing_duration_seconds',
    'PDF processing duration in seconds',
    ['file_size_category']
)

ACTIVE_SESSIONS = Gauge(
    'active_chat_sessions',
    'Number of active chat sessions'
)

VECTOR_SEARCH_DURATION = Histogram(
    'vector_search_duration_seconds',
    'Vector search duration in seconds',
    ['content_type']
)

LLM_TOKEN_USAGE = Counter(
    'llm_tokens_used_total',
    'Total tokens used by LLM',
    ['model', 'operation']
)

def monitor_request_metrics(endpoint: str):
    """Decorator to monitor request metrics"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status_code = 200
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status_code = 500
                raise
            finally:
                duration = time.time() - start_time
                
                # Get method from request context if available
                method = "POST"  # Default for API endpoints
                
                REQUEST_COUNT.labels(
                    method=method,
                    endpoint=endpoint,
                    status_code=status_code
                ).inc()
                
                REQUEST_DURATION.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)
        
        return wrapper
    return decorator

class MetricsCollector:
    """Centralized metrics collection"""
    
    @staticmethod
    def record_pdf_processing(file_size: int, duration: float):
        """Record PDF processing metrics"""
        file_size_mb = file_size / (1024 * 1024)
        
        if file_size_mb < 1:
            category = "small"
        elif file_size_mb < 10:
            category = "medium"
        elif file_size_mb < 50:
            category = "large"
        else:
            category = "xlarge"
        
        PDF_PROCESSING_DURATION.labels(file_size_category=category).observe(duration)
    
    @staticmethod
    def record_vector_search(content_type: str, duration: float):
        """Record vector search metrics"""
        VECTOR_SEARCH_DURATION.labels(content_type=content_type).observe(duration)
    
    @staticmethod
    def record_llm_usage(model: str, operation: str, tokens: int):
        """Record LLM token usage"""
        LLM_TOKEN_USAGE.labels(model=model, operation=operation).inc(tokens)
    
    @staticmethod
    def update_active_sessions(count: int):
        """Update active sessions gauge"""
        ACTIVE_SESSIONS.set(count)

metrics_collector = MetricsCollector()

def get_metrics():
    """Get Prometheus metrics"""
    return generate_latest()