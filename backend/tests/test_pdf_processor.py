import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from app.services.pdf_processor import MultimodalPDFProcessor
from app.services.vector_store import MultimodalVectorStoreService

class TestPDFProcessor:
    
    @pytest.fixture
    def pdf_processor(self):
        return MultimodalPDFProcessor(chunk_size=500, chunk_overlap=50)
    
    @pytest.fixture
    def sample_pdf_path(self):
        # Create a temporary PDF file for testing
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            # You would put actual PDF content here for real tests
            tmp.write(b'%PDF-1.4 sample content')
            return tmp.name
    
    def teardown_method(self):
        # Clean up temporary files
        pass
    
    @pytest.mark.asyncio
    async def test_extract_text_content(self, pdf_processor, sample_pdf_path):
        """Test text extraction from PDF"""
        with patch('fitz.open') as mock_fitz:
            # Mock PyMuPDF
            mock_doc = Mock()
            mock_page = Mock()
            mock_page.get_text.return_value = "Sample text content"
            mock_doc.__len__.return_value = 1
            mock_doc.__getitem__.return_value = mock_page
            mock_fitz.return_value = mock_doc
            
            result = await pdf_processor._extract_text_content(sample_pdf_path)
            
            assert len(result) == 1
            assert result[0]['content'] == "Sample text content"
            assert result[0]['page_number'] == 1
            assert result[0]['content_type'] == "text"
    
    @pytest.mark.asyncio
    async def test_extract_tables(self, pdf_processor, sample_pdf_path):
        """Test table extraction from PDF"""
        with patch('camelot.read_pdf') as mock_camelot:
            # Mock table data
            mock_table = Mock()
            mock_table.df = Mock()
            mock_table.df.empty = False
            mock_table.df.to_dict.return_value = [{'col1': 'val1', 'col2': 'val2'}]
            mock_table.page = 1
            mock_table.accuracy = 0.9
            
            mock_camelot.return_value = [mock_table]
            
            result = await pdf_processor._extract_tables(sample_pdf_path)
            
            assert len(result) >= 1
            assert result[0]['content_type'] == "table"
            assert result[0]['page_number'] == 1
    
    @pytest.mark.asyncio
    async def test_process_pdf_integration(self, pdf_processor):
        """Test complete PDF processing pipeline"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            # Mock a more complete PDF processing
            with patch.object(pdf_processor, '_extract_text_content') as mock_text, \
                 patch.object(pdf_processor, '_extract_tables') as mock_tables, \
                 patch.object(pdf_processor, '_extract_images') as mock_images, \
                 patch.object(pdf_processor, '_extract_metadata') as mock_metadata:
                
                mock_text.return_value = [{'content': 'test', 'page_number': 1, 'content_type': 'text'}]
                mock_tables.return_value = []
                mock_images.return_value = []
                mock_metadata.return_value = {'page_count': 1}
                
                result = await pdf_processor.process_pdf(tmp.name)
                
                assert 'text_chunks' in result
                assert 'tables' in result
                assert 'images' in result
                assert 'metadata' in result
                assert len(result['text_chunks']) > 0

class TestVectorStore:
    
    @pytest.fixture
    def vector_service(self):
        with patch('app.services.vector_store.EuriaiEmbeddings'):
            return MultimodalVectorStoreService()
    
    @pytest.mark.asyncio
    async def test_add_documents(self, vector_service):
        """Test adding documents to vector store"""
        from langchain.schema import Document
        
        docs = [
            Document(page_content="Test content", metadata={"page": 1}),
            Document(page_content="More content", metadata={"page": 2})
        ]
        
        with patch.object(vector_service.text_store.vector_store, 'add_documents') as mock_add:
            await vector_service.text_store.add_documents(docs)
            mock_add.assert_called_once_with(docs)
    
    @pytest.mark.asyncio
    async def test_similarity_search(self, vector_service):
        """Test similarity search"""
        from langchain.schema import Document
        
        expected_docs = [
            Document(page_content="Relevant content", metadata={"page": 1})
        ]
        
        with patch.object(vector_service.text_store.vector_store, 'similarity_search') as mock_search:
            mock_search.return_value = expected_docs
            
            result = await vector_service.text_store.similarity_search("test query", k=5)
            
            assert result == expected_docs
            mock_search.assert_called_once_with("test query", k=5)

# Test configuration
@pytest.fixture(scope="session")
def test_config():
    """Test configuration"""
    os.environ.update({
        "EURI_API_KEY": "test-key",
        "VECTOR_DB_TYPE": "chroma",
        "DATABASE_URL": "sqlite:///test.db"
    })

if __name__ == "__main__":
    pytest.main([__file__, "-v"])