import asyncio
import time
from typing import Dict, Any
from app.services.vector_store import MultimodalVectorStoreService
from app.core.config import settings
import structlog

logger = structlog.get_logger()

class HealthCheckService:
    """Service for comprehensive health checks"""
    
    def __init__(self):
        self.vector_service = MultimodalVectorStoreService()
    
    async def check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity"""
        try:
            from app.services.database import db_service
            
            start_time = time.time()
            
            # Test database connection
            with db_service.get_session() as db:
                db.execute("SELECT 1")
                
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time * 1000, 2)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def check_vector_store_health(self) -> Dict[str, Any]:
        """Check vector store connectivity"""
        try:
            start_time = time.time()
            
            # Test vector store with a simple search
            await self.vector_service.text_store.similarity_search("health check", k=1)
            
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time * 1000, 2)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def check_euri_api_health(self) -> Dict[str, Any]:
        """Check EURI AI API connectivity"""
        try:
            from euriai import EuriaiClient
            
            start_time = time.time()
            
            client = EuriaiClient(api_key=settings.EURI_API_KEY)
            
            # Test with minimal request
            response = client.generate_completion(
                prompt="test",
                max_tokens=1,
                temperature=0
            )
            
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time * 1000, 2)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        import psutil
        import os
        
        return {
            "cpu_usage_percent": psutil.cpu_percent(),
            "memory_usage_percent": psutil.virtual_memory().percent,
            "disk_usage_percent": psutil.disk_usage('/').percent,
            "process_count": len(psutil.pids()),
            "upload_dir_size_mb": self._get_dir_size(settings.UPLOAD_DIR),
            "chroma_db_size_mb": self._get_dir_size(settings.CHROMA_PERSIST_DIRECTORY)
        }
    
    def _get_dir_size(self, path: str) -> float:
        """Get directory size in MB"""
        try:
            if not os.path.exists(path):
                return 0
            
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    total_size += os.path.getsize(file_path)
            
            return round(total_size / (1024 * 1024), 2)
        except:
            return 0
    
    async def comprehensive_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        checks = {}
        
        # Run all health checks concurrently
        database_check = asyncio.create_task(self.check_database_health())
        vector_store_check = asyncio.create_task(self.check_vector_store_health())
        euri_api_check = asyncio.create_task(self.check_euri_api_health())
        system_info_task = asyncio.create_task(self.get_system_info())
        
        checks["database"] = await database_check
        checks["vector_store"] = await vector_store_check
        checks["euri_api"] = await euri_api_check
        checks["system"] = await system_info_task
        
        # Determine overall health
        overall_status = "healthy"
        if any(check.get("status") == "unhealthy" for check in checks.values() if isinstance(check, dict) and "status" in check):
            overall_status = "degraded"
        
        return {
            "overall_status": overall_status,
            "timestamp": time.time(),
            "checks": checks
        }

health_service = HealthCheckService()