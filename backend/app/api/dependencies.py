from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import jwt
import logging

from app.core.config import settings
from app.services.database import db_service

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """Get current authenticated user (optional for now)"""
    if not credentials:
        return None
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        
        user_id = payload.get("sub")
        if not user_id:
            return None
            
        # TODO: Get user from database
        return {"user_id": user_id}
        
    except jwt.PyJWTError:
        return None

async def require_auth(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Require authentication"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user

def get_db():
    """Get database session"""
    return db_service.get_session()

async def validate_document_access(
    document_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
) -> bool:
    """Validate user has access to document"""
    # For now, allow access to all documents
    # In production, implement proper access control
    document = await db_service.get_document(document_id)
    
    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )
    
    return True

async def rate_limit_check(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
) -> bool:
    """Check rate limits"""
    # TODO: Implement rate limiting
    # For now, always allow
    return True

async def validate_file_size(file_size: int) -> bool:
    """Validate uploaded file size"""
    if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB"
        )
    return True

async def validate_query_complexity(query: str) -> bool:
    """Validate query complexity to prevent abuse"""
    if len(query) > settings.MAX_QUERY_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Query too long. Maximum length: {settings.MAX_QUERY_LENGTH} characters"
        )
    
    # Check for potentially expensive operations
    expensive_keywords = ["analyze all", "process everything", "full document scan"]
    query_lower = query.lower()
    
    if any(keyword in query_lower for keyword in expensive_keywords):
        logger.warning(f"Potentially expensive query detected: {query[:100]}")
        # Could implement additional checks or user confirmation
    
    return True