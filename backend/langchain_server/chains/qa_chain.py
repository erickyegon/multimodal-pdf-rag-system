from langchain.chains.base import Chain
from langchain.schema import Document
from langchain.callbacks.manager import CallbackManagerForChainRun
from typing import Dict, List, Any, Optional
import logging
import asyncio

from app.services.vector_store import MultimodalVectorStoreService
from app.services.llm_service import AdvancedLLMService

logger = logging.getLogger(__name__)

class QAChain(Chain):
    """Question-Answering chain for PDF documents"""
    
    vector_service: MultimodalVectorStoreService
    llm_service: AdvancedLLMService
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.vector_service = MultimodalVectorStoreService()
        self.llm_service = AdvancedLLMService()
    
    @property
    def input_keys(self) -> List[str]:
        return ["question", "context_types", "max_sources"]
    
    @property
    def output_keys(self) -> List[str]:
        return ["answer", "sources", "confidence", "context_used"]
    
    def _call(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, Any]:
        """Execute the Q&A chain"""
        
        question = inputs["question"]
        context_types = inputs.get("context_types", ["text", "table"])
        max_sources = inputs.get("max_sources", 8)
        
        if run_manager:
            run_manager.on_text(f"Answering question: {question}", verbose=True)
        
        # Retrieve relevant context
        search_results = asyncio.run(
            self.vector_service.search_multimodal(
                query=question,
                content_types=context_types,
                k_per_type=max_sources // len(context_types)
            )
        )
        
        # Determine question type for better answering
        question_type = self._classify_question(question)
        
        if run_manager:
            run_manager.on_text(f"Question type: {question_type}", verbose=True)
        
        # Generate answer based on question type
        if question_type == "factual":
            answer_result = asyncio.run(
                self._answer_factual_question(question, search_results, run_manager)
            )
        elif question_type == "analytical":
            answer_result = asyncio.run(
                self._answer_analytical_question(question, search_results, run_manager)
            )
        elif question_type == "numerical":
            answer_result = asyncio.run(
                self._answer_numerical_question(question, search_results, run_manager)
            )
        else:
            answer_result = asyncio.run(
                self._answer_general_question(question, search_results, run_manager)
            )
        
        # Format sources
        sources = self._format_qa_sources(search_results)
        
        # Calculate confidence
        confidence = self._calculate_qa_confidence(
            question, 
            answer_result["answer"], 
            search_results,
            question_type
        )
        
        return {
            "answer": answer_result["answer"],
            "sources": sources,
            "confidence": confidence,
            "context_used": answer_result.get("context_used", ""),
            "question_type": question_type
        }
    
    def _classify_question(self, question: str) -> str:
        """Classify the type of question"""
        question_lower = question.lower()
        
        # Factual questions
        if any(word in question_lower for word in ["what is", "who is", "where is", "when", "define"]):
            return "factual"
        
        # Analytical questions
        elif any(word in question_lower for word in ["why", "how", "analyze", "explain", "compare"]):
            return "analytical"
        
        # Numerical/calculation questions
        elif any(word in question_lower for word in ["how much", "how many", "calculate", "total", "average"]):
            return "numerical"
        
        # List/enumeration questions
        elif any(word in question_lower for word in ["list", "name", "identify", "which"]):
            return "list"
        
        else:
            return "general"
    
    async def _answer_factual_question(
        self, 
        question: str, 
        search_results: Dict[str, List[Document]],
        run_manager: Optional[CallbackManagerForChainRun] = None
    ) -> Dict[str, Any]:
        """Answer factual questions with direct, concise responses"""
        
        # Prioritize text sources for factual questions
        text_docs = search_results.get("text", [])
        
        if not text_docs:
            return {
                "answer": "I couldn't find specific factual information to answer this question in the document.",
                "context_used": ""
            }
        
        # Build context from most relevant sources
        context = self._build_factual_context(text_docs[:5])
        
        factual_prompt = f"""
        Answer this factual question based on the provided context:
        
        Question: {question}
        
        Context: {context}
        
        Instructions:
        - Provide a direct, factual answer
        - Use exact information from the context
        - Include specific page references if available
        - If the answer isn't in the context, say so clearly
        - Keep the answer concise but complete
        """
        
        answer = await self.llm_service.generate_response(factual_prompt)
        
        return {
            "answer": answer,
            "context_used": context[:500] + "..." if len(context) > 500 else context
        }
    
    async def _answer_analytical_question(
        self, 
        question: str, 
        search_results: Dict[str, List[Document]],
        run_manager: Optional[CallbackManagerForChainRun] = None
    ) -> Dict[str, Any]:
        """Answer analytical questions requiring reasoning and explanation"""
        
        # Use all available content types for analytical questions
        all_docs = []
        for docs in search_results.values():
            all_docs.extend(docs)
        
        if not all_docs:
            return {
                "answer": "I don't have enough information in the document to provide an analytical answer to this question.",
                "context_used": ""
            }
        
        context = self._build_analytical_context(all_docs[:8])
        
        analytical_prompt = f"""
        Provide a thorough analytical answer to this question:
        
        Question: {question}
        
        Context: {context}
        
        Instructions:
        - Analyze the information deeply
        - Explain the reasoning behind your answer
        - Consider multiple perspectives if applicable
        - Use evidence from the context to support your analysis
        - Structure your answer logically
        - Be comprehensive but clear
        """
        
        answer = await self.llm_service.generate_response(analytical_prompt)
        
        return {
            "answer": answer,
            "context_used": context[:800] + "..." if len(context) > 800 else context
        }
    
    async def _answer_numerical_question(
        self, 
        question: str, 
        search_results: Dict[str, List[Document]],
        run_manager: Optional[CallbackManagerForChainRun] = None
    ) -> Dict[str, Any]:
        """Answer numerical questions requiring calculations"""
        
        # Prioritize table data for numerical questions
        table_docs = search_results.get("table", [])
        
        if not table_docs:
            return {
                "answer": "I couldn't find numerical data in the document to answer this question.",
                "context_used": ""
            }
        
        # Extract numerical data
        numerical_data = []
        for doc in table_docs:
            if "table_data" in doc.metadata:
                numerical_data.extend(doc.metadata["table_data"])
        
        context = self._build_numerical_context(numerical_data[:20])
        
        numerical_prompt = f"""
        Answer this numerical question using the provided data:
        
        Question: {question}
        
        Data: {context}
        
        Instructions:
        - Perform necessary calculations
        - Show your work step by step
        - Provide exact numbers where possible
        - Include units and context
        - Verify calculations are logical
        - If data is insufficient, explain what's missing
        """
        
        answer = await self.llm_service.generate_response(numerical_prompt)
        
        return {
            "answer": answer,
            "context_used": context[:600] + "..." if len(context) > 600 else context
        }
    
    async def _answer_general_question(
        self, 
        question: str, 
        search_results: Dict[str, List[Document]],
        run_manager: Optional[CallbackManagerForChainRun] = None
    ) -> Dict[str, Any]:
        """Answer general questions using all available context"""
        
        all_docs = []
        for docs in search_results.values():
            all_docs.extend(docs)
        
        if not all_docs:
            return {
                "answer": "I couldn't find relevant information in the document to answer this question.",
                "context_used": ""
            }
        
        context = self._build_general_context(all_docs[:6])
        
        general_prompt = f"""
        Answer this question based on the available information:
        
        Question: {question}
        
        Context: {context}
        
        Instructions:
        - Provide a helpful and informative answer
        - Use information from the context
        - Be clear and well-structured
        - Include relevant details
        - If information is limited, acknowledge it
        """
        
        answer = await self.llm_service.generate_response(general_prompt)
        
        return {
            "answer": answer,
            "context_used": context[:700] + "..." if len(context) > 700 else context
        }
    
    def _build_factual_context(self, docs: List[Document]) -> str:
        """Build context optimized for factual questions"""
        context_parts = []
        
        for doc in docs:
            page_ref = doc.metadata.get("page_number", "Unknown")
            content = doc.page_content[:300]  # Shorter for factual
            context_parts.append(f"[Page {page_ref}] {content}")
        
        return "\n\n".join(context_parts)
    
    def _build_analytical_context(self, docs: List[Document]) -> str:
        """Build context optimized for analytical questions"""
        context_parts = []
        
        for doc in docs:
            page_ref = doc.metadata.get("page_number", "Unknown")
            content_type = doc.metadata.get("content_type", "text")
            content = doc.page_content[:500]  # Longer for analysis
            context_parts.append(f"[{content_type.title()} - Page {page_ref}] {content}")
        
        return "\n\n".join(context_parts)
    
    def _build_numerical_context(self, data: List[Dict[str, Any]]) -> str:
        """Build context optimized for numerical questions"""
        if not data:
            return "No numerical data available."
        
        context_parts = []
        context_parts.append(f"Available data ({len(data)} records):")
        
        # Show structure
        if data:
            columns = list(data[0].keys())
            context_parts.append(f"Columns: {', '.join(columns)}")
        
        # Show sample data
        for i, record in enumerate(data[:5]):
            context_parts.append(f"Record {i+1}: {record}")
        
        if len(data) > 5:
            context_parts.append(f"... and {len(data) - 5} more records")
        
        return "\n".join(context_parts)
    
    def _build_general_context(self, docs: List[Document]) -> str:
        """Build general context from mixed document types"""
        context_parts = []
        
        for doc in docs:
            page_ref = doc.metadata.get("page_number", "Unknown")
            content_type = doc.metadata.get("content_type", "text")
            content = doc.page_content[:400]
            context_parts.append(f"[{content_type.title()} - Page {page_ref}] {content}")
        
        return "\n\n".join(context_parts)
    
    def _format_qa_sources(self, search_results: Dict[str, List[Document]]) -> List[str]:
        """Format sources for Q&A response"""
        sources = []
        
        for content_type, docs in search_results.items():
            for doc in docs:
                page_num = doc.metadata.get("page_number", "Unknown")
                source_text = f"Page {page_num}"
                
                if content_type != "text":
                    source_text += f" ({content_type})"
                
                sources.append(source_text)
        
        # Remove duplicates and sort
        unique_sources = list(set(sources))
        return sorted(unique_sources, key=lambda x: int(x.split()[1]) if x.split()[1].isdigit() else 999)
    
    def _calculate_qa_confidence(
        self, 
        question: str, 
        answer: str, 
        search_results: Dict[str, List[Document]],
        question_type: str
    ) -> float:
        """Calculate confidence score for Q&A response"""
        
        base_confidence = 0.6
        
        # Question type adjustments
        if question_type == "factual":
            base_confidence += 0.1  # Factual questions typically more confident
        elif question_type == "analytical":
            base_confidence -= 0.1  # Analytical questions more uncertain
        
        # Source quantity
        total_sources = sum(len(docs) for docs in search_results.values())
        if total_sources >= 5:
            base_confidence += 0.2
        elif total_sources >= 3:
            base_confidence += 0.1
        
        # Answer length (reasonable answers are usually detailed)
        if 100 < len(answer) < 1000:
            base_confidence += 0.1
        
        # Check for uncertainty indicators in answer
        uncertainty_phrases = ["i don't know", "unclear", "insufficient", "cannot determine"]
        if any(phrase in answer.lower() for phrase in uncertainty_phrases):
            base_confidence -= 0.3
        
        return max(0.1, min(1.0, base_confidence))