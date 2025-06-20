rom langchain.chains.base import Chain
from langchain.schema import Document
from langchain.callbacks.manager import CallbackManagerForChainRun
from typing import Dict, List, Any, Optional
import logging
import asyncio

from app.services.vector_store import MultimodalVectorStoreService
from app.services.llm_service import AdvancedLLMService
from app.utils.chart_generator import ChartGenerator

logger = logging.getLogger(__name__)

class AnalysisChain(Chain):
    """Chain for comprehensive document analysis"""
    
    vector_service: MultimodalVectorStoreService
    llm_service: AdvancedLLMService
    chart_generator: ChartGenerator
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.vector_service = MultimodalVectorStoreService()
        self.llm_service = AdvancedLLMService()
        self.chart_generator = ChartGenerator()
    
    @property
    def input_keys(self) -> List[str]:
        return ["query", "analysis_type", "include_visualization"]
    
    @property
    def output_keys(self) -> List[str]:
        return ["analysis", "insights", "chart_data", "confidence", "sources"]
    
    def _call(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, Any]:
        """Execute the analysis chain"""
        
        query = inputs["query"]
        analysis_type = inputs.get("analysis_type", "general")
        include_visualization = inputs.get("include_visualization", True)
        
        if run_manager:
            run_manager.on_text(f"Starting analysis for: {query}", verbose=True)
        
        # Search for relevant content
        search_results = asyncio.run(
            self.vector_service.search_multimodal(
                query=query,
                content_types=["text", "table", "image"],
                k_per_type=8
            )
        )
        
        if run_manager:
            run_manager.on_text(f"Found {sum(len(docs) for docs in search_results.values())} relevant documents", verbose=True)
        
        # Perform analysis based on type
        if analysis_type == "trend":
            analysis_result = asyncio.run(
                self._perform_trend_analysis(query, search_results, run_manager)
            )
        elif analysis_type == "comparison":
            analysis_result = asyncio.run(
                self._perform_comparison_analysis(query, search_results, run_manager)
            )
        elif analysis_type == "summary":
            analysis_result = asyncio.run(
                self._perform_summary_analysis(query, search_results, run_manager)
            )
        else:
            analysis_result = asyncio.run(
                self._perform_general_analysis(query, search_results, run_manager)
            )
        
        # Generate visualization if requested
        chart_data = {}
        if include_visualization and search_results.get("table"):
            if run_manager:
                run_manager.on_text("Generating visualization...", verbose=True)
            
            chart_result = asyncio.run(
                self.chart_generator.generate_chart_from_query(
                    query, search_results["table"]
                )
            )
            chart_data = chart_result
        
        # Extract insights
        insights = self._extract_insights(analysis_result["analysis"])
        
        return {
            "analysis": analysis_result["analysis"],
            "insights": insights,
            "chart_data": chart_data,
            "confidence": analysis_result.get("confidence", 0.8),
            "sources": self._format_sources(search_results),
            "analysis_type": analysis_type
        }
    
    async def _perform_trend_analysis(
        self, 
        query: str, 
        search_results: Dict[str, List[Document]],
        run_manager: Optional[CallbackManagerForChainRun] = None
    ) -> Dict[str, Any]:
        """Perform trend analysis"""
        
        # Focus on table data for trends
        table_docs = search_results.get("table", [])
        
        if not table_docs:
            return {
                "analysis": "No tabular data available for trend analysis.",
                "confidence": 0.2
            }
        
        # Extract time series data
        time_series_data = []
        for doc in table_docs:
            if "table_data" in doc.metadata:
                time_series_data.extend(doc.metadata["table_data"])
        
        trend_prompt = f"""
        Perform a comprehensive trend analysis for: {query}
        
        Available data: {len(time_series_data)} records
        Sample data: {time_series_data[:5] if time_series_data else "No data"}
        
        Analyze:
        1. Overall trends (increasing, decreasing, cyclical)
        2. Rate of change and acceleration
        3. Seasonal patterns
        4. Key inflection points
        5. Statistical significance
        6. Forecasting insights
        
        Provide specific numbers and percentages where possible.
        """
        
        analysis = await self.llm_service.generate_response(trend_prompt)
        
        # Calculate confidence based on data availability
        confidence = min(0.9, 0.5 + (len(time_series_data) / 100))
        
        return {
            "analysis": analysis,
            "confidence": confidence,
            "data_points": len(time_series_data)
        }
    
    async def _perform_comparison_analysis(
        self, 
        query: str, 
        search_results: Dict[str, List[Document]],
        run_manager: Optional[CallbackManagerForChainRun] = None
    ) -> Dict[str, Any]:
        """Perform comparison analysis"""
        
        all_docs = (
            search_results.get("text", []) + 
            search_results.get("table", []) + 
            search_results.get("image", [])
        )
        
        comparison_prompt = f"""
        Perform a detailed comparison analysis for: {query}
        
        Available sources: {len(all_docs)} documents
        Content types: {list(search_results.keys())}
        
        Provide:
        1. Side-by-side comparison of key metrics
        2. Percentage differences
        3. Strengths and weaknesses of each item
        4. Statistical significance of differences
        5. Ranking and recommendations
        6. Context and implications
        
        Be quantitative and specific.
        """
        
        # Build context from documents
        context = self._build_context(all_docs)
        analysis = await self.llm_service.generate_response(
            comparison_prompt, 
            context=context
        )
        
        return {
            "analysis": analysis,
            "confidence": 0.8,
            "sources_used": len(all_docs)
        }
    
    async def _perform_summary_analysis(
        self, 
        query: str, 
        search_results: Dict[str, List[Document]],
        run_manager: Optional[CallbackManagerForChainRun] = None
    ) -> Dict[str, Any]:
        """Perform summary analysis"""
        
        all_docs = (
            search_results.get("text", []) + 
            search_results.get("table", [])
        )
        
        summary_prompt = f"""
        Create a comprehensive summary for: {query}
        
        Sources: {len(all_docs)} documents
        
        Include:
        1. Key findings and main points
        2. Important statistics and numbers
        3. Critical insights and implications
        4. Executive summary
        5. Recommendations or next steps
        
        Structure the summary logically with clear sections.
        """
        
        context = self._build_context(all_docs)
        analysis = await self.llm_service.generate_response(
            summary_prompt, 
            context=context
        )
        
        return {
            "analysis": analysis,
            "confidence": 0.85,
            "documents_summarized": len(all_docs)
        }
    
    async def _perform_general_analysis(
        self, 
        query: str, 
        search_results: Dict[str, List[Document]],
        run_manager: Optional[CallbackManagerForChainRun] = None
    ) -> Dict[str, Any]:
        """Perform general analysis"""
        
        all_docs = (
            search_results.get("text", []) + 
            search_results.get("table", []) + 
            search_results.get("image", [])
        )
        
        general_prompt = f"""
        Analyze the following content to answer: {query}
        
        Available information from {len(all_docs)} sources across multiple content types.
        
        Provide:
        1. Direct answer to the question
        2. Supporting evidence and data
        3. Multiple perspectives if applicable
        4. Confidence level and limitations
        5. Additional relevant insights
        
        Be thorough and cite specific information.
        """
        
        context = self._build_context(all_docs)
        analysis = await self.llm_service.generate_response(
            general_prompt, 
            context=context
        )
        
        return {
            "analysis": analysis,
            "confidence": 0.8,
            "sources_analyzed": len(all_docs)
        }
    
    def _build_context(self, docs: List[Document]) -> str:
        """Build context string from documents"""
        context_parts = []
        
        for i, doc in enumerate(docs[:10]):  # Limit to prevent token overflow
            page_ref = doc.metadata.get("page_number", "Unknown")
            content_type = doc.metadata.get("content_type", "text")
            
            context_parts.append(
                f"[{content_type.title()} from Page {page_ref}]\n{doc.page_content[:500]}...\n"
            )
        
        return "\n".join(context_parts)
    
    def _extract_insights(self, analysis: str) -> List[str]:
        """Extract key insights from analysis"""
        insights = []
        
        # Look for numbered points or bullet points
        lines = analysis.split('\n')
        for line in lines:
            line = line.strip()
            if (line.startswith(('1.', '2.', '3.', '4.', '5.', '•', '-')) or
                any(keyword in line.lower() for keyword in 
                    ['increase', 'decrease', 'significant', 'trend', 'growth', 'decline'])):
                
                # Clean up the line
                clean_line = line.lstrip('1234567890.- •').strip()
                if len(clean_line) > 20:
                    insights.append(clean_line)
                    
                if len(insights) >= 5:
                    break
        
        return insights[:5]
    
    def _format_sources(self, search_results: Dict[str, List[Document]]) -> List[str]:
        """Format source information"""
        sources = []
        
        for content_type, docs in search_results.items():
            for doc in docs:
                page_num = doc.metadata.get("page_number", "Unknown")
                sources.append(f"Page {page_num} ({content_type})")
        
        return list(set(sources))  # Remove duplicates
