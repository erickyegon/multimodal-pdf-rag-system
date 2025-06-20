from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from app.core.config import settings
from app.models.database import Base, Document, ChatSession, ChatMessage
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        if settings.DATABASE_URL.startswith("sqlite"):
            # SQLite specific configuration
            self.engine = create_engine(
                settings.DATABASE_URL,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
        else:
            # PostgreSQL configuration
            self.engine = create_engine(settings.DATABASE_URL)
        
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    async def create_document(self, document_data: Dict[str, Any]) -> Document:
        """Create new document record"""
        with self.get_session() as db:
            document = Document(**document_data)
            db.add(document)
            db.commit()
            db.refresh(document)
            return document
    
    async def get_document(self, document_id: str) -> Optional[Document]:
        """Get document by ID"""
        with self.get_session() as db:
            return db.query(Document).filter(Document.id == document_id).first()
    
    async def list_documents(self, limit: int = 100) -> List[Document]:
        """List all documents"""
        with self.get_session() as db:
            return db.query(Document).order_by(Document.upload_date.desc()).limit(limit).all()
    
    async def update_document_status(self, document_id: str, status: str, metadata: Dict[str, Any] = None):
        """Update document processing status"""
        with self.get_session() as db:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.processing_status = status
                if metadata:
                    document.processing_metadata = metadata
                db.commit()
    
    async def create_chat_session(self, document_id: str, session_name: str = None) -> ChatSession:
        """Create new chat session"""
        with self.get_session() as db:
            session = ChatSession(
                document_id=document_id,
                session_name=session_name or f"Session {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            return session
    
    async def save_chat_message(self, message_data: Dict[str, Any]) -> ChatMessage:
        """Save chat message"""
        with self.get_session() as db:
            message = ChatMessage(**message_data)
            db.add(message)
            db.commit()
            db.refresh(message)
            return message
    
    async def get_chat_history(self, session_id: str) -> List[ChatMessage]:
        """Get chat history for session"""
        with self.get_session() as db:
            return db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.timestamp).all()
    
    async def get_document_analytics(self, document_id: str) -> Dict[str, Any]:
        """Get analytics for document"""
        with self.get_session() as db:
            # Get document
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                return {}
            
            # Get chat statistics
            total_sessions = db.query(ChatSession).filter(ChatSession.document_id == document_id).count()
            total_messages = db.query(ChatMessage).join(ChatSession).filter(
                ChatSession.document_id == document_id
            ).count()
            
            # Get average response time
            avg_response_time = db.query(ChatMessage.processing_time).join(ChatSession).filter(
                ChatSession.document_id == document_id,
                ChatMessage.message_type == "assistant",
                ChatMessage.processing_time.isnot(None)
            ).all()
            
            avg_time = sum([t[0] for t in avg_response_time if t[0]]) / len(avg_response_time) if avg_response_time else 0
            
            return {
                "document_info": {
                    "filename": document.filename,
                    "page_count": document.page_count,
                    "upload_date": document.upload_date,
                    "file_size": document.file_size
                },
                "usage_stats": {
                    "total_sessions": total_sessions,
                    "total_messages": total_messages,
                    "avg_response_time": round(avg_time, 2)
                },
                "content_stats": {
                    "text_chunks": document.text_chunks,
                    "tables_found": document.tables_found,
                    "images_found": document.images_found
                }
            }

# Global database service instance
db_service = DatabaseService()