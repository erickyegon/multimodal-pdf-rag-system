from typing import Dict, Any, List, TypedDict
from langgraph.graph import StateGraph, END
import logging
import asyncio

from app.services.analytics_service import AnalyticsService
from app.services.vector_store import MultimodalVectorStoreService
from app.services.llm_service import AdvancedLLMService
from app.utils.chart_generator import ChartGenerator

logger = logging.getLogger(__name__)

class AnalyticsState(TypedDict):
    query: str
    analysis_type: str
    raw_data: List[Dict[str, Any]]
    processed_data: Dict[str, Any]
    insights: List[str]
    charts: Dict[str, Any]
    recommendations: List[str]
    confidence: float
    error: str

class AnalyticsGraph:
    """LangGraph workflow for comprehensive analytics"""
    
    def __init__(self):
        self.analytics_service = AnalyticsService()
        self.vector_service = MultimodalVectorStoreService()
        self.llm_service = AdvancedLLMService()
        self.chart_generator = ChartGenerator()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the analytics workflow graph"""
        
        workflow = StateGraph(AnalyticsState)
        
        # Add nodes
        workflow.add_node("classify_query", self._classify_query)
        workflow.add_node("gather_data", self._gather_data)
        workflow.add_node("process_data", self._process_data)
        workflow.add_node("generate_insights", self._generate_insights)
        workflow.add_node("create_visualizations", self._create_visualizations)
        workflow.add_node("formulate_recommendations", self._formulate_recommendations)
        workflow.add_node("calculate_confidence", self._calculate_confidence)
        workflow.add_node("handle_error", self._handle_error)
        
        # Define the workflow
        workflow.set_entry_point("classify_query")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "classify_query",
            self._should_continue_after_classification,
            {
                "continue": "gather_data",
                "error": "handle_error"
            }
        )
        
        workflow.add_edge("gather_data", "process_data")
        workflow.add_edge("process_data", "generate_insights")
        workflow.add_edge("generate_insights", "create_visualizations")
        workflow.add_edge("create_visualizations", "formulate_recommendations")
        workflow.add_edge("formulate_recommendations", "calculate_confidence")
        workflow.add_edge("calculate_confidence", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    async def _classify_query(self, state: AnalyticsState) -> AnalyticsState:
        """Classify the analytics query type"""
        try:
            query = state["query"]
            analysis_type = self.analytics_service.classify_query_type(query)
            
            state["analysis_type"] = analysis_type
            logger.info(f"Classified query as: {analysis_type}")
            
        except Exception as e:
            state["error"] = f"Query classification failed: {str(e)}"
            logger.error(f"Query classification error: {str(e)}")
        
        return state
    
    async def _gather_data(self, state: AnalyticsState) -> AnalyticsState:
        """Gather relevant data from vector stores"""
        try:
            query = state["query"]
            analysis_type = state["analysis_type"]
            
            # Determine search strategy based on analysis type
            if analysis_type in ["trend_analysis", "comparison"]:
                content_types = ["table", "text"]
                k_per_type = 15
            elif analysis_type == "summary":
                content_types = ["text", "table", "image"]
                k_per_type = 10
            else:
                content_types = ["text", "table"]
                k_per_type = 8
            
            # Search for relevant content
            search_results = await self.vector_service.search_multimodal(
                query=query,
                content_types=content_types,
                k_per_type=k_per_type
            )
            
            # Extract table data
            table_data = await self.analytics_service.extract_table_data(
                search_results.get("table", [])
            )
            
            state["raw_data"] = table_data
            logger.info(f"Gathered {len(table_data)} data points from {sum(len(docs) for docs in search_results.values())} documents")
            
        except Exception as e:
            state["error"] = f"Data gathering failed: {str(e)}"
            logger.error(f"Data gathering error: {str(e)}")
        
        return state
    
    async def _process_data(self, state: AnalyticsState) -> AnalyticsState:
        """Process and analyze the gathered data"""
        try:
            query = state["query"]
            raw_data = state["raw_data"]
            analysis_type = state["analysis_type"]
            
            if not raw_data:
                state["processed_data"] = {
                    "analysis": "No relevant data found for analysis.",
                    "statistics": {},
                    "summary": "Insufficient data for meaningful analysis."
                }
                return state
            
            # Perform analysis based on type
            if analysis_type == "trend_analysis":
                processed_data = await self._process_trend_data(query, raw_data)
            elif analysis_type == "comparison":
                processed_data = await self._process_comparison_data(query, raw_data)
            elif analysis_type == "summary":
                processed_data = await self._process_summary_data(query, raw_data)
            else:
                processed_data = await self._process_general_data(query, raw_data)
            
            state["processed_data"] = processed_data
            logger.info(f"Processed data for {analysis_type} analysis")
            
        except Exception as e:
            state["error"] = f"Data processing failed: {str(e)}"
            logger.error(f"Data processing error: {str(e)}")
        
        return state
    
    async def _generate_insights(self, state: AnalyticsState) -> AnalyticsState:
        """Generate insights from processed data"""
        try:
            processed_data = state["processed_data"]
            raw_data = state["raw_data"]
            
            if "analysis" in processed_data:
                insights = await self.analytics_service.extract_insights(
                    processed_data["analysis"],
                    raw_data
                )
            else:
                insights = ["No insights could be generated from the available data."]
            
            state["insights"] = insights
            logger.info(f"Generated {len(insights)} insights")
            
        except Exception as e:
            state["error"] = f"Insight generation failed: {str(e)}"
            logger.error(f"Insight generation error: {str(e)}")
        
        return state
    
    async def _create_visualizations(self, state: AnalyticsState) -> AnalyticsState:
        """Create charts and visualizations"""
        try:
            query = state["query"]
            raw_data = state["raw_data"]
            analysis_type = state["analysis_type"]
            
            charts = {}
            
            if raw_data and analysis_type in ["trend_analysis", "comparison"]:
                # Create mock table documents for chart generation
                from langchain.schema import Document
                
                table_docs = [
                    Document(
                        page_content=f"Table data: {raw_data[:5]}",  # Sample data
                        metadata={
                            "content_type": "table",
                            "table_data": raw_data,
                            "page_number": 1
                        }
                    )
                ]
                
                chart_result = await self.chart_generator.generate_chart_from_query(
                    query, table_docs
                )
                
                if chart_result:
                    charts = chart_result
            
            state["charts"] = charts
            logger.info(f"Created visualizations: {bool(charts)}")
            
        except Exception as e:
            state["error"] = f"Visualization creation failed: {str(e)}"
            logger.error(f"Visualization creation error: {str(e)}")
        
        return state
    
    async def _formulate_recommendations(self, state: AnalyticsState) -> AnalyticsState:
        """Formulate actionable recommendations"""
        try:
            analysis = state["processed_data"].get("analysis", "")
            insights = state["insights"]
            analysis_type = state["analysis_type"]
            
            recommendations_prompt = f"""
            Based on this {analysis_type} analysis, provide 3-5 actionable recommendations:
            
            Analysis: {analysis}
            
            Key Insights: {'; '.join(insights)}
            
            Provide specific, actionable recommendations that:
            1. Address the findings
            2. Are practical to implement
            3. Have clear business value
            4. Are prioritized by impact
            
            Return as a JSON array of strings.
            """
            
            response = await self.llm_service.generate_response(recommendations_prompt)
            
            try:
                import json
                recommendations = json.loads(response)
                if not isinstance(recommendations, list):
                    recommendations = [response]
            except:
                # Fallback: split by lines
                recommendations = [line.strip() for line in response.split('\n') if line.strip()]
                recommendations = [rec for rec in recommendations if len(rec) > 10][:5]
            
            state["recommendations"] = recommendations
            logger.info(f"Generated {len(recommendations)} recommendations")
            
        except Exception as e:
            state["error"] = f"Recommendation generation failed: {str(e)}"
            logger.error(f"Recommendation generation error: {str(e)}")
        
        return state
    
    async def _calculate_confidence(self, state: AnalyticsState) -> AnalyticsState:
        """Calculate overall confidence in the analysis"""
        try:
            raw_data = state["raw_data"]
            processed_data = state["processed_data"]
            insights = state["insights"]
            charts = state["charts"]
            
            confidence = 0.5  # Base confidence
            
            # Data quantity factor
            if len(raw_data) > 50:
                confidence += 0.2
            elif len(raw_data) > 20:
                confidence += 0.1
            
            # Analysis quality factor
            if len(processed_data.get("analysis", "")) > 200:
                confidence += 0.1
            
            # Insights factor
            if len(insights) >= 3:
                confidence += 0.1
            
            # Visualization factor
            if charts:
                confidence += 0.1
            
            # Analysis type factor
            analysis_type = state["analysis_type"]
            if analysis_type in ["trend_analysis", "summary"]:
                confidence += 0.05  # These tend to be more reliable
            
            state["confidence"] = min(1.0, confidence)
            logger.info(f"Calculated confidence: {state['confidence']:.2f}")
            
        except Exception as e:
            state["error"] = f"Confidence calculation failed: {str(e)}"
            logger.error(f"Confidence calculation error: {str(e)}")
        
        return state
    
    async def _handle_error(self, state: AnalyticsState) -> AnalyticsState:
        """Handle errors in the analytics pipeline"""
        error_msg = state.get("error", "Unknown error occurred")
        logger.error(f"Analytics pipeline error: {error_msg}")
        
        # Provide fallback response
        state["processed_data"] = {
            "analysis": f"Analytics processing encountered an error: {error_msg}",
            "statistics": {},
            "summary": "Unable to complete analysis due to technical issues."
        }
        state["insights"] = ["Analysis could not be completed due to technical issues."]
        state["charts"] = {}
        state["recommendations"] = ["Please try rephrasing your query or contact support."]
        state["confidence"] = 0.1
        
        return state
    
    def _should_continue_after_classification(self, state: AnalyticsState) -> str:
        """Determine whether to continue or handle error after classification"""
        if state.get("error"):
            return "error"
        return "continue"
    
    async def _process_trend_data(self, query: str, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process data for trend analysis"""
        
        trend_analysis = await self.analytics_service.analyze_trends(
            query=query,
            time_series_analysis=True
        )
        
        return {
            "analysis": f"Trend analysis reveals: {trend_analysis}",
            "trend_data": trend_analysis,
            "statistics": self._calculate_basic_stats(data)
        }
    
    async def _process_comparison_data(self, query: str, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process data for comparison analysis"""
        
        comparison_prompt = f"""
        Perform a comparative analysis based on this query: {query}
        
        Data available: {len(data)} records
        Sample: {data[:3] if data else "No data"}
        
        Identify:
        1. Key metrics being compared
        2. Significant differences
        3. Performance rankings
        4. Statistical significance
        """
        
        analysis = await self.llm_service.generate_response(comparison_prompt)
        
        return {
            "analysis": analysis,
            "comparison_data": data,
            "statistics": self._calculate_basic_stats(data)
        }
    
    async def _process_summary_data(self, query: str, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process data for summary analysis"""
        
        stats = self._calculate_basic_stats(data)
        
        summary_prompt = f"""
        Create a comprehensive summary for: {query}
        
        Data overview:
        - Records: {len(data)}
        - Statistics: {stats}
        
        Provide:
        1. Key highlights
        2. Important patterns
        3. Notable findings
        4. Overall assessment
        """
        
        analysis = await self.llm_service.generate_response(summary_prompt)
        
        return {
            "analysis": analysis,
            "summary_stats": stats,
            "statistics": stats
        }
    
    async def _process_general_data(self, query: str, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process data for general analysis"""
        
        general_prompt = f"""
        Analyze the data to answer: {query}
        
        Available data: {len(data)} records
        Sample data: {data[:5] if data else "No data"}
        
        Provide a thorough analysis addressing the query.
        """
        
        analysis = await self.llm_service.generate_response(general_prompt)
        
        return {
            "analysis": analysis,
            "data_overview": {"record_count": len(data)},
            "statistics": self._calculate_basic_stats(data)
        }
    
    def _calculate_basic_stats(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate basic statistics for the data"""
        if not data:
            return {}
        
        return {
            "total_records": len(data),
            "columns": list(set().union(*(d.keys() for d in data))) if data else [],
            "sample_record": data[0] if data else {}
        }
    
    async def process_analytics_query(self, query: str, analysis_type: str = None) -> Dict[str, Any]:
        """Process an analytics query through the graph"""
        
        initial_state = AnalyticsState(
            query=query,
            analysis_type=analysis_type or "",
            raw_data=[],
            processed_data={},
            insights=[],
            charts={},
            recommendations=[],
            confidence=0.0,
            error=""
        )
        
        try:
            result = await self.graph.ainvoke(initial_state)
            
            return {
                "query": query,
                "analysis_type": result["analysis_type"],
                "analysis": result["processed_data"].get("analysis", ""),
                "insights": result["insights"],
                "charts": result["charts"],
                "recommendations": result["recommendations"],
                "confidence": result["confidence"],
                "data_points": len(result["raw_data"]),
                "error": result.get("error", "")
            }
            
        except Exception as e:
            logger.error(f"Analytics graph execution error: {str(e)}")
            return {
                "query": query,
                "analysis": f"Analytics processing failed: {str(e)}",
                "insights": [],
                "charts": {},
                "recommendations": [],
                "confidence": 0.1,
                "data_points": 0,
                "error": str(e)
            }