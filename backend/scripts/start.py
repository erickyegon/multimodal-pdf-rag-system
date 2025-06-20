"""
Startup script for the multimodal PDF RAG system
"""

import asyncio
import sys
import os
import subprocess
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.services.database import db_service
from app.services.vector_store import MultimodalVectorStoreService

async def check_dependencies():
    """Check if all dependencies are installed"""
    try:
        import uvicorn
        import fastapi
        import langchain
        import euriai
        print("✅ All Python dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False

async def check_external_services():
    """Check external service connectivity"""
    print("🔍 Checking external services...")
    
    # Check EURI AI
    if not settings.EURI_API_KEY:
        print("⚠️  EURI_API_KEY not configured")
        return False
    
    try:
        from euriai import EuriaiClient
        client = EuriaiClient(api_key=settings.EURI_API_KEY)
        # Test with minimal request
        response = client.generate_completion(prompt="test", max_tokens=1)
        print("✅ EURI AI service is accessible")
    except Exception as e:
        print(f"❌ EURI AI service error: {str(e)}")
        return False
    
    return True

async def initialize_database():
    """Initialize database and create tables"""
    print("🗄️  Initializing database...")
    
    try:
        # Database initialization happens in db_service constructor
        db_service.get_session().close()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {str(e)}")
        return False

async def initialize_vector_store():
    """Initialize vector store"""
    print("🔍 Initializing vector store...")
    
    try:
        vector_service = MultimodalVectorStoreService()
        print(f"✅ Vector store ({settings.VECTOR_DB_TYPE}) initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Vector store initialization failed: {str(e)}")
        return False

async def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    
    directories = [
        settings.UPLOAD_DIR,
        settings.PROCESSED_DIR,
        settings.CHROMA_PERSIST_DIRECTORY
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Directory created: {directory}")
    
    return True

async def run_health_check():
    """Run comprehensive health check"""
    print("🏥 Running health check...")
    
    checks = [
        ("Dependencies", check_dependencies()),
        ("Directories", create_directories()),
        ("Database", initialize_database()),
        ("Vector Store", initialize_vector_store()),
        ("External Services", check_external_services())
    ]
    
    results = []
    for name, check in checks:
        print(f"\n🔍 {name}...")
        result = await check
        results.append((name, result))
        
        if result:
            print(f"✅ {name}: OK")
        else:
            print(f"❌ {name}: FAILED")
    
    return all(result for _, result in results)

def start_server():
    """Start the FastAPI server"""
    print("\n🚀 Starting server...")
    
    cmd = [
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000"
    ]
    
    if settings.DEBUG:
        cmd.extend(["--reload", "--log-level", "debug"])
    else:
        cmd.extend(["--workers", "4", "--log-level", "info"])
    
    try:
        subprocess.run(cmd, cwd=project_root)
    except KeyboardInterrupt:
        print("\n⏹️  Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {str(e)}")

async def main():
    """Main startup function"""
    print(f"🎯 Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    print("=" * 50)
    
    # Run health check
    if await run_health_check():
        print("\n🎉 All systems ready!")
        print("=" * 50)
        
        # Start server
        start_server()
    else:
        print("\n💥 Startup failed! Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())