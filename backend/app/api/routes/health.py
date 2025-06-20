from fastapi import APIRouter
from app.services.health import health_service
from app.monitoring.prometheus import get_metrics
from fastapi.responses import PlainTextResponse

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "service": "multimodal-pdf-rag"}

@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with all components"""
    return await health_service.comprehensive_health_check()

@router.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe"""
    health_status = await health_service.comprehensive_health_check()
    
    if health_status["overall_status"] in ["healthy", "degraded"]:
        return {"status": "ready"}
    else:
        return {"status": "not_ready"}, 503

@router.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe"""
    return {"status": "alive"}

@router.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint"""
    return PlainTextResponse(get_metrics(), media_type="text/plain")