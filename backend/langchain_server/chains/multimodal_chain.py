from langchain.chains.base import Chain
from langchain.schema import Document
from langchain.callbacks.manager import CallbackManagerForChainRun
from typing import Dict, List, Any, Optional
import logging
import asyncio

from app.services.multimodal_processor import MultimodalProcessor
from app.services.vector_store import MultimodalVectorStoreService

logger = logging.getLogger(__name__)

class MultimodalChain(Chain):
    """Chain for processing multimodal queries across text, tables, and images"""
    
    multimodal_processor: MultimodalProcessor
    vector_service: MultimodalVectorStoreService
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.multimodal_processor = MultimodalProcessor()
        self.vector_service = MultimodalVectorStoreService()
    
    @property
    def input_keys(self) -> List[str]:
        return ["query", "content_types", "k_per_type"]
    
    @property
    def output_keys(self) -> List[str]:
        return ["response", "modality_results", "synthesis", "confidence", "sources"]
    
    def _call(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, Any]:
        """Execute the multimodal chain"""
        
        query = inputs["query"]
        content_types = inputs.get("content_types", ["text", "table", "image"])
        k_per_type = inputs.get("k_per_type", 5)
        
        if run_manager:
            run_manager.on_text(f"Processing multimodal query: {query}", verbose=True)
        
        # Detect query intent and optimize retrieval
        intent = asyncio.run(
            self.multimodal_processor.detect_query_intent(query)
        )
        
        if run_manager:
            run_manager.on_text(f"Detected intent: {intent.get('primary_intent', 'unknown')}", verbose=True)
        
        # Retrieve relevant content from all modalities
        search_results = asyncio.run(
            self.vector_service.search_multimodal(
                query=query,
                content_types=content_types,
                k_per_type=k_per_type
            )
        )
        
        total_results = sum(len(docs) for docs in search_results.values())
        if run_manager:
            run_manager.on_text(f"Retrieved {total_results} documents across modalities", verbose=True)
        
        # Process through multimodal processor
        multimodal_result = asyncio.run(
            self.multimodal_processor.process_multimodal_query(
                query=query,
                text_docs=search_results.get("text", []),
                table_docs=search_results.get("table", []),
                image_docs=search_results.get("image", [])
            )
        )
        
        # Calculate overall confidence
        confidence = self._calculate_confidence(
            multimodal_result, 
            search_results, 
            intent
        )
        
        # Format sources
        sources = self._format_multimodal_sources(search_results)
        
        return {
            "response": multimodal_result["synthesis"],
            "modality_results": multimodal_result["modality_results"],
            "synthesis": multimodal_result["synthesis"],
            "confidence": confidence,
            "sources": sources,
            "intent": intent,
            "relevance_scores": multimodal_result["relevance_scores"]
        }
    
    def _calculate_confidence(
        self, 
        multimodal_result: Dict[str, Any],
        search_results: Dict[str, List[Document]],
        intent: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for multimodal response"""
        
        base_confidence = 0.5
        
        # More modalities = higher confidence
        active_modalities = len(multimodal_result["modality_results"])
        base_confidence += active_modalities * 0.1
        
        # More documents = higher confidence
        total_docs = sum(len(docs) for docs in search_results.values())
        if total_docs > 5:
            base_confidence += 0.2
        elif total_docs > 2:
            base_confidence += 0.1
        
        # Intent match = higher confidence
        if intent.get("complexity") == "simple":
            base_confidence += 0.1
        
        # Relevance scores
        relevance_scores = multimodal_result.get("relevance_scores", {})
        avg_relevance = sum(relevance_scores.values()) / len(relevance_scores) if relevance_scores else 0.5
        base_confidence += avg_relevance * 0.2
        
        return min(1.0, base_confidence)
    
    def _format_multimodal_sources(self, search_results: Dict[str, List[Document]]) -> List[Dict[str, Any]]:
        """Format source information for multimodal results"""
        sources = []
        
        for content_type, docs in search_results.items():
            for doc in docs:
                source_info = {
                    "content_type": content_type,
                    "page_number": doc.metadata.get("page_number", "Unknown"),
                    "relevance": getattr(doc, 'relevance_score', 0.8)
                }
                
                # Add specific metadata based on content type
                if content_type == "table":
                    source_info["table_id"] = doc.metadata.get("table_id")
                    source_info["extraction_method"] = doc.metadata.get("extraction_method")
                elif content_type == "image":
                    source_info["image_id"] = doc.metadata.get("image_id")
                    source_info["has_ocr"] = bool(doc.metadata.get("ocr_text"))
                
                sources.append(source_info)
        
        return sources
