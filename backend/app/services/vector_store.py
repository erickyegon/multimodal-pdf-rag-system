from typing import List, Dict, Any, Optional
import os
import pickle
from langchain_community.vectorstores import Chroma, FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from euriai.langchain_embed import EuriaiEmbeddings
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class VectorStoreService:
    def __init__(self):
        try:
            self.embeddings = EuriaiEmbeddings(
                api_key=settings.EURI_API_KEY,
                model=settings.EURI_EMBEDDING_MODEL
            )
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {str(e)}")
            # Fallback to a different embedding service or disable embeddings
            raise
        self.vector_store = None
        self._initialize_vector_store()
    
    def _initialize_vector_store(self):
        """Initialize the vector store based on configuration"""
        if settings.VECTOR_DB_TYPE.lower() == "chroma":
            os.makedirs(settings.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
            self.vector_store = Chroma(
                persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
                embedding_function=self.embeddings
            )
        elif settings.VECTOR_DB_TYPE.lower() == "faiss":
            os.makedirs(os.path.dirname(settings.FAISS_INDEX_PATH), exist_ok=True)
            if os.path.exists(settings.FAISS_INDEX_PATH + ".pkl"):
                self.vector_store = FAISS.load_local(
                    settings.FAISS_INDEX_PATH,
                    self.embeddings
                )
            else:
                # Create empty FAISS index
                self.vector_store = FAISS.from_texts(
                    ["dummy"], self.embeddings
                )
                self.vector_store.delete([0])  # Remove dummy text
    
    async def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the vector store"""
        try:
            logger.info(f"Adding {len(documents)} documents to vector store")
            
            if settings.VECTOR_DB_TYPE.lower() == "chroma":
                self.vector_store.add_documents(documents)
                self.vector_store.persist()
            elif settings.VECTOR_DB_TYPE.lower() == "faiss":
                self.vector_store.add_documents(documents)
                self.vector_store.save_local(settings.FAISS_INDEX_PATH)
            
            logger.info("Documents successfully added to vector store")
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {str(e)}")
            raise
    
    async def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Perform similarity search with error handling"""
        try:
            if filter_dict and settings.VECTOR_DB_TYPE.lower() == "chroma":
                results = self.vector_store.similarity_search(
                    query, k=k, filter=filter_dict
                )
            else:
                results = self.vector_store.similarity_search(query, k=k)

            return results

        except Exception as e:
            logger.error(f"Error performing similarity search: {str(e)}")
            # Return empty results instead of crashing
            if "400" in str(e) or "500" in str(e):
                logger.warning("API error encountered, returning empty search results")
                return []
            raise
    
    async def similarity_search_with_score(
        self, 
        query: str, 
        k: int = 5
    ) -> List[tuple]:
        """Perform similarity search with scores"""
        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)
            return results
            
        except Exception as e:
            logger.error(f"Error performing similarity search with score: {str(e)}")
            raise

class MultimodalVectorStoreService:
    def __init__(self):
        self.text_store = VectorStoreService()
        self.table_store = VectorStoreService()
        self.image_store = VectorStoreService()
    
    async def add_multimodal_content(self, processed_content: Dict[str, Any]):
        """Add multimodal content to appropriate vector stores"""
        # Add text chunks
        if processed_content.get("text_chunks"):
            await self.text_store.add_documents(processed_content["text_chunks"])
        
        # Process and add tables
        if processed_content.get("tables"):
            table_documents = self._process_tables_for_vectorization(
                processed_content["tables"]
            )
            await self.table_store.add_documents(table_documents)
        
        # Process and add images
        if processed_content.get("images"):
            image_documents = self._process_images_for_vectorization(
                processed_content["images"]
            )
            await self.image_store.add_documents(image_documents)
    
    def _process_tables_for_vectorization(self, tables: List[Dict[str, Any]]) -> List[Document]:
        """Convert tables to documents for vectorization"""
        documents = []
        
        for table in tables:
            # Convert table to text representation
            table_text = self._table_to_text(table["content"])
            
            doc = Document(
                page_content=table_text,
                metadata={
                    "page_number": table["page_number"],
                    "content_type": "table",
                    "table_id": table["table_id"],
                    "extraction_method": table["extraction_method"],
                    "source": "pdf_table"
                }
            )
            documents.append(doc)
        
        return documents
    
    def _process_images_for_vectorization(self, images: List[Dict[str, Any]]) -> List[Document]:
        """Convert images to documents for vectorization using OCR text"""
        documents = []
        
        for image in images:
            if image["ocr_text"].strip():
                doc = Document(
                    page_content=image["ocr_text"],
                    metadata={
                        "page_number": image["page_number"],
                        "content_type": "image",
                        "image_id": image["image_id"],
                        "source": "pdf_image_ocr"
                    }
                )
                documents.append(doc)
        
        return documents
    
    def _table_to_text(self, table_data: List[Dict[str, Any]]) -> str:
        """Convert table data to text representation"""
        if not table_data:
            return ""
        
        # Get column headers
        headers = list(table_data[0].keys())
        text_parts = [f"Table with columns: {', '.join(headers)}"]
        
        # Add row data
        for row in table_data[:10]:  # Limit to first 10 rows for vectorization
            row_text = " | ".join([f"{k}: {v}" for k, v in row.items() if v])
            text_parts.append(row_text)
        
        return "\n".join(text_parts)
    
    async def search_multimodal(
        self, 
        query: str, 
        content_types: List[str] = ["text", "table", "image"],
        k_per_type: int = 3
    ) -> Dict[str, List[Document]]:
        """Search across all content types"""
        results = {}
        
        if "text" in content_types:
            results["text"] = await self.text_store.similarity_search(query, k=k_per_type)
        
        if "table" in content_types:
            results["table"] = await self.table_store.similarity_search(query, k=k_per_type)
        
        if "image" in content_types:
            results["image"] = await self.image_store.similarity_search(query, k=k_per_type)
        
        return results