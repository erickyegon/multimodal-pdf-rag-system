import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import tempfile
import os

from app.main import app

client = TestClient(app)

class TestChatAPI:
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    @patch('app.api.routes.chat.rag_graph')
    def test_chat_endpoint(self, mock_rag_graph):
        """Test chat endpoint"""
        # Mock RAG graph response
        mock_rag_graph.process_query.return_value = {
            "response": "Test response",
            "chart_data": {},
            "sources": ["Page 1"],
            "metadata": {}
        }
        
        response = client.post(
            "/api/v1/chat/chat",
            json={"query": "What is the main topic?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "Test response"
        assert "sources" in data
    
    def test_chat_endpoint_invalid_request(self):
        """Test chat endpoint with invalid request"""
        response = client.post(
            "/api/v1/chat/chat",
            json={}  # Missing query
        )
        
        assert response.status_code == 422  # Validation error

class TestUploadAPI:
    
    @patch('app.services.pdf_processor.MultimodalPDFProcessor.process_pdf')
    @patch('app.services.vector_store.MultimodalVectorStoreService.add_multimodal_content')
    def test_upload_pdf(self, mock_add_content, mock_process_pdf):
        """Test PDF upload endpoint"""
        # Mock processing results
        mock_process_pdf.return_value = {
            "metadata": {"page_count": 10},
            "text_chunks": ["chunk1", "chunk2"],
            "tables": [],
            "images": []
        }
        
        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            tmp.write(b'%PDF-1.4 test content')
            tmp.seek(0)
            
            response = client.post(
                "/api/v1/upload/upload",
                files={"file": ("test.pdf", tmp, "application/pdf")}
            )
        
        os.unlink(tmp.name)  # Clean up
        
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.pdf"
        assert data["page_count"] == 10
    
    def test_upload_invalid_file_type(self):
        """Test upload with invalid file type"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as tmp:
            tmp.write(b'text content')
            tmp.seek(0)
            
            response = client.post(
                "/api/v1/upload/upload",
                files={"file": ("test.txt", tmp, "text/plain")}
            )
        
        os.unlink(tmp.name)
        
        assert response.status_code == 400

class TestAnalyticsAPI:
    
    @patch('app.services.llm_service.AdvancedLLMService.analyze_trends')
    @patch('app.services.vector_store.MultimodalVectorStoreService')
    def test_analytics_endpoint(self, mock_vector_service, mock_analyze_trends):
        """Test analytics endpoint"""
        # Mock vector search results
        mock_vector_service.table_store.similarity_search.return_value = []
        
        # Mock trend analysis
        mock_analyze_trends.return_value = {
            "analysis": "Test analysis",
            "insights": ["Insight 1", "Insight 2"]
        }
        
        response = client.post(
            "/api/v1/analytics/analytics",
            json={
                "query": "Show trends in revenue",
                "generate_chart": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "analysis" in data
        assert "insights" in data