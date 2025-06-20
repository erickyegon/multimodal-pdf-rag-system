from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from datetime import datetime, timezone
import uuid

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    page_count = Column(Integer, nullable=True, default=0)
    upload_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    processing_status = Column(String, default="pending")  # pending, processing, completed, failed
    processing_metadata = Column(JSON)
    
    # Content statistics
    text_chunks = Column(Integer, default=0)
    tables_found = Column(Integer, default=0)
    images_found = Column(Integer, default=0)
    
    # Relationships
    chat_sessions = relationship("ChatSession", back_populates="document")
    analytics_queries = relationship("AnalyticsQuery", back_populates="document")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    session_name = Column(String)
    created_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_activity = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    document = relationship("Document", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    message_type = Column(String, nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Response metadata
    sources = Column(JSON)  # Source pages and content types
    chart_data = Column(JSON)  # Chart configuration if generated
    processing_time = Column(Float)  # Response time in seconds
    token_count = Column(Integer)  # Tokens used
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")

class AnalyticsQuery(Base):
    __tablename__ = "analytics_queries"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    query = Column(Text, nullable=False)
    query_type = Column(String)  # trend_analysis, data_extraction, visualization
    result = Column(JSON)
    chart_config = Column(JSON)
    created_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    execution_time = Column(Float)
    
    # Relationships
    document = relationship("Document", back_populates="analytics_queries")

class VectorChunk(Base):
    __tablename__ = "vector_chunks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    content_type = Column(String, nullable=False)  # text, table, image_ocr
    page_number = Column(Integer)
    embedding_vector = Column(Text)  # Serialized vector
    chunk_metadata = Column(JSON)
    
    # Document relationship
    document = relationship("Document")

class SystemMetrics(Base):
    __tablename__ = "system_metrics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    metric_name = Column(String, nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String)
    tags = Column(JSON)  # Additional metadata