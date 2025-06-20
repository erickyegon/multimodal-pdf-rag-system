import asyncio
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
import json
import logging
import re
from datetime import datetime, timedelta
import numpy as np

from app.services.llm_service import AdvancedLLMService
from app.services.vector_store import MultimodalVectorStoreService
from langchain.schema import Document

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Advanced analytics service for document data"""
    
    def __init__(self):
        self.llm_service = AdvancedLLMService()
        self.vector_service = MultimodalVectorStoreService()
    
    async def extract_table_data(self, table_docs: List[Document]) -> List[Dict[str, Any]]:
        """Extract and structure table data from documents"""
        all_data = []
        
        for doc in table_docs:
            try:
                # Try to parse table data from metadata
                if "table_data" in doc.metadata:
                    table_data = doc.metadata["table_data"]
                    if isinstance(table_data, list):
                        all_data.extend(table_data)
                else:
                    # Parse from content
                    parsed_data = self._parse_table_content(doc.page_content)
                    all_data.extend(parsed_data)
                    
            except Exception as e:
                logger.warning(f"Error extracting table data: {str(e)}")
        
        return all_data
    
    def _parse_table_content(self, content: str) -> List[Dict[str, Any]]:
        """Parse table content from text"""
        data = []
        lines = content.split('\n')
        
        for line in lines:
            if '|' in line:
                # Parse pipe-separated values
                parts = [part.strip() for part in line.split('|')]
                if len(parts) >= 2:
                    try:
                        record = {}
                        for part in parts:
                            if ':' in part:
                                key, value = part.split(':', 1)
                                # Try to convert to number
                                try:
                                    value = float(value.strip().replace(',', '').replace('$', ''))
                                except:
                                    value = value.strip()
                                record[key.strip()] = value
                        
                        if record:
                            data.append(record)
                    except Exception as e:
                        logger.warning(f"Error parsing table row: {str(e)}")
        
        return data
    
    async def analyze_data(
        self, 
        query: str, 
        table_data: List[Dict[str, Any]],
        context_docs: List[Document] = None
    ) -> Dict[str, Any]:
        """Perform comprehensive data analysis"""
        
        # Classify the query type
        query_type = self.classify_query_type(query)
        
        # Build context for LLM
        context = self._build_analysis_context(table_data, context_docs)
        
        # Generate analysis based on query type
        if query_type == "trend_analysis":
            analysis = await self._analyze_trends(query, table_data, context)
        elif query_type == "comparison":
            analysis = await self._analyze_comparisons(query, table_data, context)
        elif query_type == "summary":
            analysis = await self._generate_summary(query, table_data, context)
        else:
            analysis = await self._general_analysis(query, table_data, context)
        
        return {
            "analysis": analysis,
            "query_type": query_type,
            "data_points": len(table_data),
            "confidence": self._calculate_confidence(table_data, analysis)
        }
    
    def classify_query_type(self, query: str) -> str:
        """Classify the type of analytics query"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["trend", "over time", "timeline", "change", "growth"]):
            return "trend_analysis"
        elif any(word in query_lower for word in ["compare", "vs", "versus", "difference", "between"]):
            return "comparison"
        elif any(word in query_lower for word in ["summary", "overview", "summarize", "total", "average"]):
            return "summary"
        elif any(word in query_lower for word in ["predict", "forecast", "future", "projection"]):
            return "prediction"
        else:
            return "general"
    
    async def _analyze_trends(
        self, 
        query: str, 
        data: List[Dict[str, Any]], 
        context: str
    ) -> str:
        """Analyze trends in the data"""
        
        # Try to identify time series data
        time_series = self._extract_time_series(data)
        
        trend_prompt = f"""
        Analyze the following data for trends and patterns:
        
        Query: {query}
        
        Data Summary:
        - Total records: {len(data)}
        - Time series data available: {bool(time_series)}
        
        Context: {context}
        
        Please provide a detailed trend analysis including:
        1. Overall trends (increasing, decreasing, stable)
        2. Seasonal patterns if any
        3. Key inflection points
        4. Rate of change
        5. Statistical significance
        
        Focus on answering the specific question while providing supporting evidence.
        """
        
        analysis = await self.llm_service.generate_response(
            prompt=trend_prompt,
            context=context
        )
        
        return analysis
    
    async def _analyze_comparisons(
        self, 
        query: str, 
        data: List[Dict[str, Any]], 
        context: str
    ) -> str:
        """Analyze comparisons in the data"""
        
        comparison_prompt = f"""
        Perform a comparative analysis of the data:
        
        Query: {query}
        
        Data available: {len(data)} records
        Context: {context}
        
        Please provide:
        1. Key differences between compared items
        2. Percentage changes where applicable
        3. Statistical significance of differences
        4. Ranking if relevant
        5. Recommendations based on comparison
        
        Be specific and use actual numbers from the data.
        """
        
        analysis = await self.llm_service.generate_response(
            prompt=comparison_prompt,
            context=context
        )
        
        return analysis
    
    async def _generate_summary(
        self, 
        query: str, 
        data: List[Dict[str, Any]], 
        context: str
    ) -> str:
        """Generate data summary"""
        
        # Calculate basic statistics
        stats = self._calculate_basic_stats(data)
        
        summary_prompt = f"""
        Generate a comprehensive summary of the data:
        
        Query: {query}
        
        Data Statistics:
        {json.dumps(stats, indent=2)}
        
        Context: {context}
        
        Please provide:
        1. Key metrics and totals
        2. Average, median, and ranges
        3. Notable patterns or outliers
        4. Overall insights
        5. Data quality assessment
        
        Make it actionable and easy to understand.
        """
        
        analysis = await self.llm_service.generate_response(
            prompt=summary_prompt,
            context=context
        )
        
        return analysis
    
    async def _general_analysis(
        self, 
        query: str, 
        data: List[Dict[str, Any]], 
        context: str
    ) -> str:
        """General purpose data analysis"""
        
        analysis_prompt = f"""
        Analyze the data to answer the following question:
        
        Question: {query}
        
        Available data: {len(data)} records
        Context: {context}
        
        Please provide:
        1. Direct answer to the question
        2. Supporting evidence from the data
        3. Relevant calculations or metrics
        4. Additional insights that might be valuable
        5. Confidence level in the analysis
        
        Be thorough but concise.
        """
        
        analysis = await self.llm_service.generate_response(
            prompt=analysis_prompt,
            context=context
        )
        
        return analysis
    
    def _build_analysis_context(
        self, 
        table_data: List[Dict[str, Any]], 
        text_docs: List[Document] = None
    ) -> str:
        """Build context for analysis"""
        context_parts = []
        
        # Add table data summary
        if table_data:
            context_parts.append("TABLE DATA:")
            
            # Sample records
            sample_size = min(5, len(table_data))
            for i, record in enumerate(table_data[:sample_size]):
                context_parts.append(f"Record {i+1}: {json.dumps(record)}")
            
            if len(table_data) > sample_size:
                context_parts.append(f"... and {len(table_data) - sample_size} more records")
            
            # Data structure info
            if table_data:
                columns = set()
                for record in table_data:
                    columns.update(record.keys())
                context_parts.append(f"Available columns: {', '.join(columns)}")
        
        # Add text context
        if text_docs:
            context_parts.append("\nTEXT CONTEXT:")
            for i, doc in enumerate(text_docs[:3]):  # Limit to 3 docs
                context_parts.append(f"Document {i+1}: {doc.page_content[:200]}...")
        
        return "\n".join(context_parts)
    
    def _extract_time_series(self, data: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
        """Extract time series data if available"""
        if not data:
            return None
        
        # Look for date/time columns
        date_columns = []
        for record in data[:5]:  # Check first 5 records
            for key, value in record.items():
                if any(word in key.lower() for word in ["date", "time", "year", "month", "day"]):
                    date_columns.append(key)
        
        if not date_columns:
            return None
        
        # Try to parse dates and sort
        try:
            time_series = []
            for record in data:
                for date_col in date_columns:
                    if date_col in record:
                        # Try to parse date
                        date_value = record[date_col]
                        if isinstance(date_value, str):
                            # Try common date formats
                            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%Y", "%m/%Y"]:
                                try:
                                    parsed_date = datetime.strptime(date_value, fmt)
                                    time_series.append({
                                        "date": parsed_date,
                                        "data": record
                                    })
                                    break
                                except:
                                    continue
            
            if time_series:
                return sorted(time_series, key=lambda x: x["date"])
        
        except Exception as e:
            logger.warning(f"Error extracting time series: {str(e)}")
        
        return None
    
    def _calculate_basic_stats(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate basic statistics for the data"""
        if not data:
            return {}
        
        stats = {
            "total_records": len(data),
            "columns": list(set().union(*(d.keys() for d in data))),
            "numeric_columns": [],
            "text_columns": [],
            "statistics": {}
        }
        
        # Analyze each column
        for col in stats["columns"]:
            values = [record.get(col) for record in data if record.get(col) is not None]
            
            if not values:
                continue
            
            # Check if numeric
            numeric_values = []
            for val in values:
                try:
                    if isinstance(val, (int, float)):
                        numeric_values.append(float(val))
                    else:
                        # Try to parse as number
                        clean_val = str(val).replace(',', '').replace('$', '').strip()
                        numeric_values.append(float(clean_val))
                except:
                    pass
            
            if len(numeric_values) > len(values) * 0.7:  # If 70% are numeric
                stats["numeric_columns"].append(col)
                stats["statistics"][col] = {
                    "count": len(numeric_values),
                    "mean": np.mean(numeric_values),
                    "median": np.median(numeric_values),
                    "std": np.std(numeric_values),
                    "min": np.min(numeric_values),
                    "max": np.max(numeric_values)
                }
            else:
                stats["text_columns"].append(col)
                stats["statistics"][col] = {
                    "count": len(values),
                    "unique_values": len(set(values)),
                    "most_common": max(set(values), key=values.count) if values else None
                }
        
        return stats
    
    def _calculate_confidence(self, data: List[Dict[str, Any]], analysis: str) -> float:
        """Calculate confidence score for the analysis"""
        confidence = 0.5  # Base confidence
        
        # More data = higher confidence
        if len(data) > 100:
            confidence += 0.2
        elif len(data) > 50:
            confidence += 0.1
        
        # Presence of numeric data increases confidence
        numeric_count = 0
        if data:
            for record in data[:10]:
                for value in record.values():
                    try:
                        float(str(value).replace(',', '').replace('$', ''))
                        numeric_count += 1
                    except:
                        pass
        
        if numeric_count > 10:
            confidence += 0.2
        
        # Analysis length and detail
        if len(analysis) > 500:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    async def extract_insights(
        self, 
        analysis: str, 
        data: List[Dict[str, Any]]
    ) -> List[str]:
        """Extract key insights from analysis"""
        
        insights_prompt = f"""
        Extract 3-5 key actionable insights from this analysis:
        
        Analysis: {analysis}
        
        Data points: {len(data)}
        
        Return insights as a JSON array of strings. Each insight should be:
        1. Specific and actionable
        2. Based on the data
        3. Business-relevant
        4. Concise (1-2 sentences)
        
        Example format:
        ["Revenue increased by 15% year-over-year", "Q4 showed strongest growth at 23%"]
        """
        
        response = await self.llm_service.generate_response(insights_prompt)
        
        try:
            insights = json.loads(response)
            return insights if isinstance(insights, list) else [response]
        except:
            # Fallback: extract insights manually
            return self._extract_insights_fallback(analysis)
    
    def _extract_insights_fallback(self, analysis: str) -> List[str]:
        """Fallback method to extract insights"""
        sentences = analysis.split('. ')
        insights = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and any(word in sentence.lower() for word in 
                                       ["increase", "decrease", "trend", "significant", 
                                        "growth", "decline", "improvement", "higher", "lower"]):
                insights.append(sentence + ('.' if not sentence.endswith('.') else ''))
                
                if len(insights) >= 5:
                    break
        
        return insights[:5]
    
    async def analyze_trends(
        self, 
        query: str, 
        time_series_analysis: bool = True
    ) -> Dict[str, Any]:
        """Specialized trend analysis"""
        
        # Search for time-related data
        search_results = await self.vector_service.search_multimodal(
            query=f"{query} timeline date time year month",
            content_types=["table"],
            k_per_type=15
        )
        
        table_data = await self.extract_table_data(search_results.get("table", []))
        time_series = self._extract_time_series(table_data)
        
        trends = {
            "trends": [],
            "forecast": None,
            "seasonality": None,
            "anomalies": [],
            "confidence": 0.5
        }
        
        if time_series:
            trends.update(await self._analyze_time_series(time_series, query))
        
        return trends
    
    async def _analyze_time_series(
        self, 
        time_series: List[Dict[str, Any]], 
        query: str
    ) -> Dict[str, Any]:
        """Analyze time series data"""
        
        # Extract numeric trends
        trends = []
        
        # Sort by date
        sorted_data = sorted(time_series, key=lambda x: x["date"])
        
        # Look for numeric columns to analyze
        if sorted_data:
            sample_data = sorted_data[0]["data"]
            numeric_cols = []
            
            for key, value in sample_data.items():
                try:
                    float(str(value).replace(',', '').replace('$', ''))
                    numeric_cols.append(key)
                except:
                    pass
            
            # Analyze each numeric column
            for col in numeric_cols:
                values = []
                dates = []
                
                for item in sorted_data:
                    try:
                        val = float(str(item["data"].get(col, 0)).replace(',', '').replace('$', ''))
                        values.append(val)
                        dates.append(item["date"])
                    except:
                        continue
                
                if len(values) > 1:
                    # Calculate trend
                    if values[-1] > values[0]:
                        direction = "increasing"
                        change = ((values[-1] - values[0]) / values[0]) * 100
                    elif values[-1] < values[0]:
                        direction = "decreasing"
                        change = ((values[0] - values[-1]) / values[0]) * 100
                    else:
                        direction = "stable"
                        change = 0
                    
                    trends.append({
                        "column": col,
                        "direction": direction,
                        "change_percent": round(change, 2),
                        "start_value": values[0],
                        "end_value": values[-1],
                        "data_points": len(values)
                    })
        
        return {
            "trends": trends,
            "data_points": len(time_series),
            "date_range": {
                "start": min(item["date"] for item in sorted_data).isoformat() if sorted_data else None,
                "end": max(item["date"] for item in sorted_data).isoformat() if sorted_data else None
            }
        }
    
    async def compare_datasets(
        self, 
        query: str, 
        dataset_a_query: str, 
        dataset_b_query: str
    ) -> Dict[str, Any]:
        """Compare two datasets"""
        
        # Search for both datasets
        data_a_results = await self.vector_service.search_multimodal(
            query=dataset_a_query,
            content_types=["table"],
            k_per_type=10
        )
        
        data_b_results = await self.vector_service.search_multimodal(
            query=dataset_b_query,
            content_types=["table"],
            k_per_type=10
        )
        
        data_a = await self.extract_table_data(data_a_results.get("table", []))
        data_b = await self.extract_table_data(data_b_results.get("table", []))
        
        comparison = await self._perform_comparison(data_a, data_b, query)
        
        return comparison
    
    async def _perform_comparison(
        self, 
        data_a: List[Dict[str, Any]], 
        data_b: List[Dict[str, Any]], 
        query: str
    ) -> Dict[str, Any]:
        """Perform detailed comparison between datasets"""
        
        comparison_prompt = f"""
        Compare these two datasets and answer: {query}
        
        Dataset A: {len(data_a)} records
        Sample: {json.dumps(data_a[:3], indent=2) if data_a else "No data"}
        
        Dataset B: {len(data_b)} records  
        Sample: {json.dumps(data_b[:3], indent=2) if data_b else "No data"}
        
        Provide:
        1. Key differences
        2. Similarities
        3. Quantitative comparisons
        4. Which dataset performs better (if applicable)
        5. Recommendations
        """
        
        analysis = await self.llm_service.generate_response(comparison_prompt)
        
        return {
            "comparison": analysis,
            "dataset_a_size": len(data_a),
            "dataset_b_size": len(data_b),
            "query": query
        }
    
    async def get_document_metrics(self, document_id: str) -> Dict[str, Any]:
        """Get comprehensive metrics for a document"""
        
        # Get document from database
        from app.services.database import db_service
        analytics = await db_service.get_document_analytics(document_id)
        
        if not analytics:
            raise ValueError("Document not found")
        
        return {
            **analytics,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def export_analysis(
        self, 
        query: str, 
        format: str = "json",
        include_charts: bool = True
    ) -> Dict[str, Any]:
        """Export analysis results"""
        
        # Run full analysis
        search_results = await self.vector_service.search_multimodal(
            query=query,
            content_types=["text", "table", "image"],
            k_per_type=10
        )
        
        table_data = await self.extract_table_data(search_results.get("table", []))
        analysis_result = await self.analyze_data(query, table_data, search_results.get("text", []))
        insights = await self.extract_insights(analysis_result["analysis"], table_data)
        
        export_data = {
            "query": query,
            "analysis": analysis_result["analysis"],
            "insights": insights,
            "data_summary": {
                "records_analyzed": len(table_data),
                "sources": len(search_results.get("text", [])) + len(search_results.get("table", [])),
                "query_type": analysis_result["query_type"],
                "confidence": analysis_result["confidence"]
            },
            "generated_at": datetime.utcnow().isoformat(),
            "format": format
        }
        
        if include_charts:
            # Generate chart data
            from app.utils.chart_generator import ChartGenerator
            chart_generator = ChartGenerator()
            chart_data = await chart_generator.generate_chart_from_query(
                query, search_results.get("table", [])
            )
            export_data["chart_data"] = chart_data
        
        return export_data