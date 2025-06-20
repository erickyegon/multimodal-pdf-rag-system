from typing import List, Dict, Any, Optional
from euriai import EuriaiClient
from euriai.langchain_llm import EuriaiLangChainLLM
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langchain.callbacks.base import BaseCallbackHandler
from app.core.config import settings
import logging
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.client = EuriaiClient(
            api_key=settings.EURI_API_KEY,
            model=settings.EURI_MODEL
        )
        
        self.langchain_llm = EuriaiLangChainLLM(
            api_key=settings.EURI_API_KEY,
            model=settings.EURI_MODEL,
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_TOKENS
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate_response(
        self,
        prompt: str,
        context: str = "",
        system_message: str = ""
    ) -> str:
        """Generate response using EURI AI with retry logic"""
        try:
            full_prompt = self._build_prompt(prompt, context, system_message)

            response = self.client.generate_completion(
                prompt=full_prompt,
                temperature=settings.TEMPERATURE,
                max_tokens=settings.MAX_TOKENS
            )

            return response

        except Exception as e:
            logger.error(f"EURI AI API error: {str(e)}")
            if "500" in str(e) or "400" in str(e):
                # Log the full error for debugging
                logger.error(f"Full API error details: {e}")
            raise
    
    async def generate_with_langchain(
        self,
        messages: List[BaseMessage]
    ) -> str:
        """Generate response using LangChain integration"""
        try:
            response = await self.langchain_llm.ainvoke(messages)
            return response
            
        except Exception as e:
            logger.error(f"Error generating LangChain response: {str(e)}")
            raise
    
    def _build_prompt(self, query: str, context: str, system_message: str) -> str:
        """Build comprehensive prompt for PDF Q&A"""
        base_system = """
        You are an expert AI assistant specialized in analyzing PDF documents. 
        You have access to multimodal content including text, tables, and images from the document.
        
        Guidelines:
        1. Provide accurate, detailed responses based on the provided context
        2. If asked about trends or data analysis, provide structured insights
        3. Use specific page references when available
        4. If information is not in the context, clearly state that
        5. For numerical data, be precise and cite sources
        6. Organize responses clearly with headers when appropriate
        """
        
        if system_message:
            base_system += f"\n\nAdditional instructions: {system_message}"
        
        prompt = f"""
        {base_system}
        
        Context from PDF:
        {context}
        
        User Question: {query}
        
        Please provide a comprehensive, accurate response based on the context provided.
        If the question involves data analysis or trends, structure your response clearly.
        """
        
        return prompt

class AdvancedLLMService(LLMService):
    """Extended LLM service with advanced capabilities"""
    
    async def analyze_trends(
        self, 
        query: str, 
        table_data: List[Dict[str, Any]],
        context: str = ""
    ) -> Dict[str, Any]:
        """Analyze trends in tabular data"""
        
        system_message = """
        You are a data analyst. Analyze the provided tabular data for trends, patterns, and insights.
        Structure your response as:
        1. Summary of findings
        2. Key trends identified
        3. Statistical observations
        4. Recommendations or implications
        
        Be specific and cite data points.
        """
        
        # Format table data for analysis
        table_context = self._format_tables_for_analysis(table_data)
        full_context = f"{context}\n\nTable Data:\n{table_context}"
        
        response = await self.generate_response(
            prompt=query,
            context=full_context,
            system_message=system_message
        )
        
        return {
            "analysis": response,
            "data_points": len(table_data),
            "query": query
        }
    
    async def generate_chart_specifications(
        self, 
        query: str, 
        table_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate chart specifications based on data and query"""
        
        chart_prompt = f"""
        Based on the user query: "{query}"
        And the following table data structure: {self._get_table_structure(table_data)}
        
        Generate chart specifications in this JSON format:
        {{
            "chart_type": "line|bar|pie|scatter|histogram",
            "x_axis": "column_name",
            "y_axis": "column_name",
            "title": "Chart Title",
            "description": "What this chart shows"
        }}
        
        Choose the most appropriate chart type for the data and query.
        """
        
        response = await self.generate_response(chart_prompt)
        
        try:
            import json
            chart_spec = json.loads(response)
            return chart_spec
        except:
            # Fallback if JSON parsing fails
            return {
                "chart_type": "bar",
                "title": "Data Visualization",
                "description": "Generated chart based on query"
            }
    
    def _format_tables_for_analysis(self, tables: List[Dict[str, Any]]) -> str:
        """Format table data for LLM analysis"""
        formatted_tables = []
        
        for i, table in enumerate(tables):
            table_text = f"Table {i+1}:\n"
            
            if isinstance(table, dict) and "content" in table:
                content = table["content"]
                if isinstance(content, list) and content:
                    # Get headers
                    headers = list(content[0].keys())
                    table_text += f"Columns: {', '.join(headers)}\n"
                    
                    # Add sample rows
                    for j, row in enumerate(content[:5]):  # First 5 rows
                        row_text = " | ".join([f"{k}: {v}" for k, v in row.items()])
                        table_text += f"Row {j+1}: {row_text}\n"
                    
                    if len(content) > 5:
                        table_text += f"... and {len(content) - 5} more rows\n"
            
            formatted_tables.append(table_text)
        
        return "\n\n".join(formatted_tables)
    
    def _get_table_structure(self, tables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get table structure for chart generation"""
        if not tables:
            return {}
        
        # Use first table for structure
        table = tables[0]
        if isinstance(table, dict) and "content" in table and table["content"]:
            content = table["content"]
            if isinstance(content, list) and content:
                return {
                    "columns": list(content[0].keys()),
                    "row_count": len(content),
                    "sample_data": content[0]
                }
        
        return {}