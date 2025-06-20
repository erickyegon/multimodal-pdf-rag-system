import asyncio
from typing import List, Dict, Any, Optional, Tuple
import logging
import base64
from io import BytesIO
import numpy as np
from PIL import Image
import cv2

from app.services.llm_service import AdvancedLLMService
from langchain.schema import Document

logger = logging.getLogger(__name__)

class MultimodalProcessor:
    """Advanced multimodal processing for complex document analysis"""
    
    def __init__(self):
        self.llm_service = AdvancedLLMService()
    
    async def process_multimodal_query(
        self, 
        query: str,
        text_docs: List[Document],
        table_docs: List[Document],
        image_docs: List[Document]
    ) -> Dict[str, Any]:
        """Process query across all modalities"""
        
        # Analyze which modalities are most relevant
        modality_relevance = await self._analyze_modality_relevance(query)
        
        # Process each modality based on relevance
        results = {}
        
        if modality_relevance.get("text", 0) > 0.3 and text_docs:
            results["text"] = await self._process_text_modality(query, text_docs)
        
        if modality_relevance.get("table", 0) > 0.3 and table_docs:
            results["table"] = await self._process_table_modality(query, table_docs)
        
        if modality_relevance.get("image", 0) > 0.3 and image_docs:
            results["image"] = await self._process_image_modality(query, image_docs)
        
        # Synthesize results
        synthesis = await self._synthesize_multimodal_results(query, results)
        
        return {
            "synthesis": synthesis,
            "modality_results": results,
            "relevance_scores": modality_relevance
        }
    
    async def _analyze_modality_relevance(self, query: str) -> Dict[str, float]:
        """Determine which modalities are most relevant for the query"""
        
        relevance_prompt = f"""
        Analyze this query and determine the relevance of different content types:
        
        Query: "{query}"
        
        Rate the relevance of each content type from 0.0 to 1.0:
        
        Text content: For questions about written descriptions, explanations, narratives
        Table/Data content: For questions about numbers, statistics, comparisons, trends
        Image content: For questions about visual elements, diagrams, charts, photos
        
        Return as JSON:
        {{
            "text": 0.0-1.0,
            "table": 0.0-1.0, 
            "image": 0.0-1.0
        }}
        """
        
        response = await self.llm_service.generate_response(relevance_prompt)
        
        try:
            import json
            relevance = json.loads(response)
            
            # Ensure all values are between 0 and 1
            for key in ["text", "table", "image"]:
                if key not in relevance:
                    relevance[key] = 0.5
                relevance[key] = max(0.0, min(1.0, float(relevance[key])))
            
            return relevance
            
        except Exception as e:
            logger.warning(f"Error parsing modality relevance: {str(e)}")
            # Default relevance
            return {"text": 0.6, "table": 0.7, "image": 0.4}
    
    async def _process_text_modality(
        self, 
        query: str, 
        text_docs: List[Document]
    ) -> Dict[str, Any]:
        """Process text-based documents"""
        
        # Combine and summarize text content
        combined_text = "\n\n".join([doc.page_content for doc in text_docs[:5]])
        
        text_prompt = f"""
        Based on the following text content, answer this question: {query}
        
        Text Content:
        {combined_text[:3000]}  # Limit for token efficiency
        
        Provide a comprehensive answer based solely on the text content.
        Include relevant quotes and page references where available.
        """
        
        response = await self.llm_service.generate_response(text_prompt)
        
        return {
            "response": response,
            "source_count": len(text_docs),
            "pages_referenced": [doc.metadata.get("page_number") for doc in text_docs if doc.metadata.get("page_number")]
        }
    
    async def _process_table_modality(
        self, 
        query: str, 
        table_docs: List[Document]
    ) -> Dict[str, Any]:
        """Process table/data content"""
        
        # Extract and structure table data
        table_data = []
        for doc in table_docs:
            if "table_data" in doc.metadata:
                table_data.extend(doc.metadata["table_data"])
        
        if not table_data:
            return {"response": "No structured table data found", "data_points": 0}
        
        table_prompt = f"""
        Analyze this table data to answer: {query}
        
        Data: {table_data[:10]}  # Show first 10 records
        Total records: {len(table_data)}
        
        Provide:
        1. Direct answer to the question
        2. Relevant calculations or statistics
        3. Key patterns or trends
        4. Data quality assessment
        
        Be specific and use actual numbers from the data.
        """
        
        response = await self.llm_service.generate_response(table_prompt)
        
        # Calculate basic statistics
        stats = self._calculate_table_stats(table_data)
        
        return {
            "response": response,
            "data_points": len(table_data),
            "statistics": stats,
            "tables_analyzed": len(table_docs)
        }
    
    async def _process_image_modality(
        self, 
        query: str, 
        image_docs: List[Document]
    ) -> Dict[str, Any]:
        """Process image content using OCR and description"""
        
        image_analyses = []
        
        for doc in image_docs:
            analysis = await self._analyze_single_image(query, doc)
            if analysis:
                image_analyses.append(analysis)
        
        if not image_analyses:
            return {"response": "No relevant image content found", "images_analyzed": 0}
        
        # Synthesize image analyses
        synthesis_prompt = f"""
        Based on analysis of {len(image_analyses)} images, answer: {query}
        
        Image Analyses:
        {chr(10).join([f"Image {i+1}: {analysis['description']}" for i, analysis in enumerate(image_analyses)])}
        
        Provide a comprehensive answer based on the visual content.
        """
        
        response = await self.llm_service.generate_response(synthesis_prompt)
        
        return {
            "response": response,
            "images_analyzed": len(image_analyses),
            "image_details": image_analyses
        }
    
    async def _analyze_single_image(
        self, 
        query: str, 
        image_doc: Document
    ) -> Optional[Dict[str, Any]]:
        """Analyze a single image document"""
        
        try:
            # Get OCR text if available
            ocr_text = image_doc.metadata.get("ocr_text", "")
            page_number = image_doc.metadata.get("page_number", "Unknown")
            
            # Analyze image content
            image_prompt = f"""
            Analyze this image content in relation to the query: "{query}"
            
            OCR Text from image: {ocr_text}
            Page: {page_number}
            
            Describe:
            1. What the image shows
            2. How it relates to the query
            3. Key information extracted
            4. Any text or data visible
            """
            
            description = await self.llm_service.generate_response(image_prompt)
            
            return {
                "page_number": page_number,
                "ocr_text": ocr_text,
                "description": description,
                "relevance": self._calculate_image_relevance(query, ocr_text, description)
            }
            
        except Exception as e:
            logger.warning(f"Error analyzing image: {str(e)}")
            return None
    
    def _calculate_image_relevance(self, query: str, ocr_text: str, description: str) -> float:
        """Calculate how relevant an image is to the query"""
        
        query_terms = set(query.lower().split())
        
        # Check OCR text relevance
        ocr_terms = set(ocr_text.lower().split()) if ocr_text else set()
        ocr_overlap = len(query_terms.intersection(ocr_terms))
        
        # Check description relevance
        desc_terms = set(description.lower().split())
        desc_overlap = len(query_terms.intersection(desc_terms))
        
        # Calculate relevance score
        max_overlap = len(query_terms)
        if max_overlap == 0:
            return 0.5
        
        relevance = (ocr_overlap + desc_overlap) / (2 * max_overlap)
        return min(1.0, relevance)
    
    async def _synthesize_multimodal_results(
        self, 
        query: str, 
        results: Dict[str, Any]
    ) -> str:
        """Synthesize results from all modalities"""
        
        if not results:
            return "No relevant content found to answer the query."
        
        synthesis_prompt = f"""
        Synthesize information from multiple sources to answer: {query}
        
        Available Information:
        """
        
        if "text" in results:
            synthesis_prompt += f"\nText Analysis: {results['text']['response']}\n"
        
        if "table" in results:
            synthesis_prompt += f"\nData Analysis: {results['table']['response']}\n"
        
        if "image" in results:
            synthesis_prompt += f"\nImage Analysis: {results['image']['response']}\n"
        
        synthesis_prompt += """
        
        Provide a comprehensive, unified answer that:
        1. Directly addresses the query
        2. Integrates insights from all available sources
        3. Highlights key findings and evidence
        4. Notes any conflicting information
        5. Provides confidence level in the answer
        
        Be thorough but concise.
        """
        
        synthesis = await self.llm_service.generate_response(synthesis_prompt)
        
        return synthesis
    
    def _calculate_table_stats(self, table_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate basic statistics for table data"""
        
        if not table_data:
            return {}
        
        stats = {
            "total_records": len(table_data),
            "columns": list(set().union(*(d.keys() for d in table_data))),
            "numeric_summaries": {}
        }
        
        # Calculate stats for numeric columns
        for col in stats["columns"]:
            numeric_values = []
            
            for record in table_data:
                value = record.get(col)
                if value is not None:
                    try:
                        # Try to convert to number
                        if isinstance(value, (int, float)):
                            numeric_values.append(float(value))
                        else:
                            clean_val = str(value).replace(',', '').replace('$', '').strip()
                            numeric_values.append(float(clean_val))
                    except:
                        pass
            
            if numeric_values and len(numeric_values) > len(table_data) * 0.5:  # If >50% numeric
                stats["numeric_summaries"][col] = {
                    "count": len(numeric_values),
                    "mean": np.mean(numeric_values),
                    "median": np.median(numeric_values),
                    "min": np.min(numeric_values),
                    "max": np.max(numeric_values),
                    "sum": np.sum(numeric_values)
                }
        
        return stats
    
    async def enhance_query_with_context(
        self, 
        query: str, 
        document_metadata: Dict[str, Any]
    ) -> str:
        """Enhance query with document context"""
        
        context_info = []
        
        if document_metadata.get("title"):
            context_info.append(f"Document: {document_metadata['title']}")
        
        if document_metadata.get("page_count"):
            context_info.append(f"Pages: {document_metadata['page_count']}")
        
        if document_metadata.get("content_types"):
            context_info.append(f"Content types: {', '.join(document_metadata['content_types'])}")
        
        if context_info:
            enhanced_query = f"{query}\n\nDocument context: {'; '.join(context_info)}"
            return enhanced_query
        
        return query
    
    async def detect_query_intent(self, query: str) -> Dict[str, Any]:
        """Detect the intent and requirements of a query"""
        
        intent_prompt = f"""
        Analyze this query and determine the user's intent:
        
        Query: "{query}"
        
        Classify the intent and return as JSON:
        {{
            "primary_intent": "question_answering|data_analysis|summarization|comparison|visualization",
            "requires_calculations": true/false,
            "requires_visualization": true/false,
            "complexity": "simple|moderate|complex",
            "expected_response_type": "text|table|chart|multimodal",
            "key_entities": ["entity1", "entity2"],
            "temporal_aspect": true/false
        }}
        """
        
        response = await self.llm_service.generate_response(intent_prompt)
        
        try:
            import json
            intent = json.loads(response)
            return intent
        except:
            # Fallback intent analysis
            return self._analyze_intent_fallback(query)
    
    def _analyze_intent_fallback(self, query: str) -> Dict[str, Any]:
        """Fallback intent analysis using keyword matching"""
        
        query_lower = query.lower()
        
        # Determine primary intent
        if any(word in query_lower for word in ["what", "how", "why", "explain", "describe"]):
            primary_intent = "question_answering"
        elif any(word in query_lower for word in ["analyze", "trend", "pattern", "statistics"]):
            primary_intent = "data_analysis"
        elif any(word in query_lower for word in ["summary", "summarize", "overview"]):
            primary_intent = "summarization"
        elif any(word in query_lower for word in ["compare", "vs", "versus", "difference"]):
            primary_intent = "comparison"
        elif any(word in query_lower for word in ["chart", "graph", "plot", "visualize"]):
            primary_intent = "visualization"
        else:
            primary_intent = "question_answering"
        
        # Detect other aspects
        requires_calculations = any(word in query_lower for word in 
                                 ["calculate", "sum", "average", "total", "percentage", "growth"])
        
        requires_visualization = any(word in query_lower for word in 
                                   ["chart", "graph", "plot", "visualize", "show", "trend"])
        
        temporal_aspect = any(word in query_lower for word in 
                             ["time", "year", "month", "date", "timeline", "over time"])
        
        # Determine complexity
        if len(query.split()) > 20 or query.count('?') > 1:
            complexity = "complex"
        elif len(query.split()) > 10:
            complexity = "moderate"
        else:
            complexity = "simple"
        
        return {
            "primary_intent": primary_intent,
            "requires_calculations": requires_calculations,
            "requires_visualization": requires_visualization,
            "complexity": complexity,
            "expected_response_type": "multimodal" if requires_visualization else "text",
            "temporal_aspect": temporal_aspect
        }