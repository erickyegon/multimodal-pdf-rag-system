from typing import List, Dict, Any, TypedDict
from langgraph.graph import StateGraph, END
from langchain.schema import Document
from app.services.vector_store import MultimodalVectorStoreService
from app.services.llm_service import AdvancedLLMService
from app.utils.chart_generator import ChartGenerator
import logging

logger = logging.getLogger(__name__)

class RAGState(TypedDict):
    query: str
    retrieved_docs: Dict[str, List[Document]]
    context: str
    response: str
    chart_data: Dict[str, Any]
    metadata: Dict[str, Any]

class MultimodalRAGGraph:
    def __init__(self):
        self.vector_service = MultimodalVectorStoreService()
        self.llm_service = AdvancedLLMService()
        self.chart_generator = ChartGenerator()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the RAG workflow graph"""
        workflow = StateGraph(RAGState)
        
        # Add nodes
        workflow.add_node("retrieve", self._retrieve_documents)
        workflow.add_node("analyze_query", self._analyze_query)
        workflow.add_node("generate_context", self._generate_context)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("generate_charts", self._generate_charts)
        workflow.add_node("finalize", self._finalize_response)
        
        # Add edges
        workflow.set_entry_point("analyze_query")
        workflow.add_edge("analyze_query", "retrieve")
        workflow.add_edge("retrieve", "generate_context")
        workflow.add_edge("generate_context", "generate_response")
        workflow.add_edge("generate_response", "generate_charts")
        workflow.add_edge("generate_charts", "finalize")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    async def _analyze_query(self, state: RAGState) -> RAGState:
        """Analyze the query to determine content types needed"""
        query = state["query"].lower()
        
        # Determine what content types to search
        content_types = ["text"]  # Always search text
        
        if any(keyword in query for keyword in ["table", "data", "statistics", "numbers", "trend", "chart"]):
            content_types.append("table")
        
        if any(keyword in query for keyword in ["image", "figure", "diagram", "photo", "picture"]):
            content_types.append("image")
        
        state["metadata"] = {
            "content_types": content_types,
            "requires_charts": any(keyword in query for keyword in ["trend", "chart", "graph", "visualization"])
        }
        
        return state
    
    async def _retrieve_documents(self, state: RAGState) -> RAGState:
        """Retrieve relevant documents from vector stores"""
        try:
            content_types = state["metadata"]["content_types"]
            
            retrieved_docs = await self.vector_service.search_multimodal(
                query=state["query"],
                content_types=content_types,
                k_per_type=5
            )
            
            state["retrieved_docs"] = retrieved_docs
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            state["retrieved_docs"] = {}
        
        return state
    
    async def _generate_context(self, state: RAGState) -> RAGState:
        """Generate comprehensive context from retrieved documents"""
        context_parts = []
        
        for content_type, docs in state["retrieved_docs"].items():
            if docs:
                context_parts.append(f"\n=== {content_type.upper()} CONTENT ===")
                
                for i, doc in enumerate(docs):
                    page_ref = doc.metadata.get("page_number", "Unknown")
                    context_parts.append(f"\n[{content_type.title()} from Page {page_ref}]")
                    context_parts.append(doc.page_content)
        
        state["context"] = "\n".join(context_parts)
        return state
    
    async def _generate_response(self, state: RAGState) -> RAGState:
        """Generate response using LLM"""
        try:
            response = await self.llm_service.generate_response(
                prompt=state["query"],
                context=state["context"]
            )
            
            state["response"] = response
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            state["response"] = "I apologize, but I encountered an error while generating the response."
        
        return state
    
    async def _generate_charts(self, state: RAGState) -> RAGState:
        """Generate charts if needed"""
        if not state["metadata"].get("requires_charts", False):
            state["chart_data"] = {}
            return state
        
        try:
            # Extract table data from retrieved documents
            table_docs = state["retrieved_docs"].get("table", [])
            
            if table_docs:
                # Get table data for chart generation
                chart_data = await self.chart_generator.generate_chart_from_query(
                    query=state["query"],
                    table_docs=table_docs
                )
                
                state["chart_data"] = chart_data
            else:
                state["chart_data"] = {}
        
        except Exception as e:
            logger.error(f"Error generating charts: {str(e)}")
            state["chart_data"] = {}
        
        return state
    
    async def _finalize_response(self, state: RAGState) -> RAGState:
        """Finalize the response with metadata"""
        # Add source information
        sources = []
        for content_type, docs in state["retrieved_docs"].items():
            for doc in docs:
                page_num = doc.metadata.get("page_number", "Unknown")
                sources.append(f"Page {page_num} ({content_type})")
        
        if sources:
            state["response"] += f"\n\n**Sources:** {', '.join(set(sources))}"
        
        return state
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process a query through the RAG graph"""
        initial_state = RAGState(
            query=query,
            retrieved_docs={},
            context="",
            response="",
            chart_data={},
            metadata={}
        )
        
        result = await self.graph.ainvoke(initial_state)
        
        return {
            "response": result["response"],
            "chart_data": result["chart_data"],
            "sources": list(result["retrieved_docs"].keys()),
            "metadata": result["metadata"]
        }