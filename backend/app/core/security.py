from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from passlib.handlers.pbkdf2 import pbkdf2_sha256
import secrets
import hashlib
import hmac
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class SecurityManager:
    """Centralized security management"""
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash"""
        return pwd_context.hash(password)
    
    def create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            self.secret_key, 
            algorithm=self.algorithm
        )
        
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.PyJWTError as e:
            logger.warning(f"Token verification failed: {str(e)}")
            return None
    
    def generate_api_key(self, length: int = 32) -> str:
        """Generate secure API key"""
        return secrets.token_urlsafe(length)
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def verify_api_key(self, api_key: str, hashed_key: str) -> bool:
        """Verify API key against hash"""
        return hmac.compare_digest(
            hashlib.sha256(api_key.encode()).hexdigest(),
            hashed_key
        )
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize uploaded filename"""
        # Remove potentially dangerous characters
        import re
        import os
        
        # Get file extension
        name, ext = os.path.splitext(filename)
        
        # Remove/replace dangerous characters
        sanitized_name = re.sub(r'[^\w\s-]', '', name)
        sanitized_name = re.sub(r'[-\s]+', '-', sanitized_name)
        
        # Limit length
        if len(sanitized_name) > 100:
            sanitized_name = sanitized_name[:100]
        
        return f"{sanitized_name}{ext}"
    
    def validate_file_type(self, filename: str, allowed_types: list) -> bool:
        """Validate file type"""
        import os
        
        _, ext = os.path.splitext(filename.lower())
        return ext in allowed_types
    
    def generate_csrf_token(self) -> str:
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)
    
    def verify_csrf_token(self, token: str, stored_token: str) -> bool:
        """Verify CSRF token"""
        return hmac.compare_digest(token, stored_token)

# Global security manager instance
security_manager = SecurityManager()

# Utility functions
def get_password_hash(password: str) -> str:
    """Convenience function for password hashing"""
    return security_manager.get_password_hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Convenience function for password verification"""
    return security_manager.verify_password(plain_password, hashed_password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Convenience function for token creation"""
    return security_manager.create_access_token(data, expires_delta)

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Convenience function for token verification"""
    return security_manager.verify_token(token)

class InputValidator:
    """Input validation utilities"""
    
    @staticmethod
    def validate_query(query: str) -> bool:
        """Validate user query for safety"""
        if not query or len(query.strip()) == 0:
            return False
        
        if len(query) > settings.MAX_QUERY_LENGTH:
            return False
        
        # Check for SQL injection patterns
        sql_patterns = [
            "select ", "insert ", "update ", "delete ", "drop ", 
            "union ", "exec ", "execute ", "script ", "javascript:"
        ]
        
        query_lower = query.lower()
        for pattern in sql_patterns:
            if pattern in query_lower:
                logger.warning(f"Potentially malicious query detected: {query[:50]}")
                return False
        
        return True
    
    @staticmethod
    def validate_document_id(doc_id: str) -> bool:
        """Validate document ID format"""
        import re
        
        # Should be UUID format
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        return bool(re.match(uuid_pattern, doc_id, re.IGNORECASE))
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """Sanitize user input"""
        import html
        
        # HTML escape
        sanitized = html.escape(text)
        
        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')
        
        return sanitized

# Global validator instance
input_validator = InputValidator()