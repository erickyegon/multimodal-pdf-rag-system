import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict, Any, Optional
import json
import re
from langchain.schema import Document
import logging

logger = logging.getLogger(__name__)

class ChartGenerator:
    def __init__(self):
        self.chart_types = {
            "line": self._create_line_chart,
            "bar": self._create_bar_chart,
            "pie": self._create_pie_chart,
            "scatter": self._create_scatter_chart,
            "histogram": self._create_histogram
        }
    
    async def generate_chart_from_query(
        self, 
        query: str, 
        table_docs: List[Document]
    ) -> Dict[str, Any]:
        """Generate chart based on query and table data"""
        try:
            # Extract table data from documents
            table_data = self._extract_table_data(table_docs)
            
            if not table_data:
                return {}
            
            # Determine chart type and configuration
            chart_config = self._analyze_query_for_chart_type(query, table_data)
            
            # Generate chart
            chart = await self._create_chart(table_data, chart_config)
            
            return {
                "chart": chart,
                "config": chart_config,
                "data_summary": self._get_data_summary(table_data)
            }
            
        except Exception as e:
            logger.error(f"Error generating chart: {str(e)}")
            return {}
    
    def _extract_table_data(self, table_docs: List[Document]) -> List[Dict[str, Any]]:
        """Extract structured table data from documents"""
        all_data = []
        
        for doc in table_docs:
            try:
                # Try to extract table data from metadata or content
                if "table_data" in doc.metadata:
                    data = doc.metadata["table_data"]
                else:
                    # Parse content if it's structured
                    data = self._parse_table_content(doc.page_content)
                
                if data:
                    all_data.extend(data)
                    
            except Exception as e:
                logger.warning(f"Error extracting table data: {str(e)}")
        
        return all_data
    
    def _parse_table_content(self, content: str) -> List[Dict[str, Any]]:
        """Parse table content from text"""
        lines = content.split('\n')
        data = []
        
        # Look for structured data patterns
        for line in lines:
            if '|' in line:
                # Parse pipe-separated values
                parts = [part.strip() for part in line.split('|')]
                if len(parts) >= 2:
                    try:
                        # Try to create a record
                        if ':' in parts[0]:
                            key_value_pairs = {}
                            for part in parts:
                                if ':' in part:
                                    key, value = part.split(':', 1)
                                    key_value_pairs[key.strip()] = value.strip()
                            if key_value_pairs:
                                data.append(key_value_pairs)
                    except:
                        continue
        
        return data
    
    def _analyze_query_for_chart_type(
        self, 
        query: str, 
        data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze query to determine appropriate chart type"""
        query_lower = query.lower()
        
        # Get data columns
        if not data:
            return {"chart_type": "bar", "title": "Data Visualization"}
        
        columns = list(data[0].keys())
        numeric_columns = self._identify_numeric_columns(data)
        
        # Determine chart type based on query keywords
        if any(keyword in query_lower for keyword in ["trend", "over time", "timeline", "progression"]):
            chart_type = "line"
        elif any(keyword in query_lower for keyword in ["distribution", "frequency"]):
            chart_type = "histogram"
        elif any(keyword in query_lower for keyword in ["relationship", "correlation"]):
            chart_type = "scatter"
        elif any(keyword in query_lower for keyword in ["percentage", "proportion", "share"]):
            chart_type = "pie"
        else:
            chart_type = "bar"
        
        # Determine axes
        x_axis = columns[0] if columns else None
        y_axis = numeric_columns[0] if numeric_columns else (columns[1] if len(columns) > 1 else None)
        
        return {
            "chart_type": chart_type,
            "x_axis": x_axis,
            "y_axis": y_axis,
            "title": self._generate_chart_title(query, chart_type),
            "description": f"Chart showing {query}"
        }
    
    def _identify_numeric_columns(self, data: List[Dict[str, Any]]) -> List[str]:
        """Identify numeric columns in the data"""
        if not data:
            return []
        
        numeric_columns = []
        
        for column in data[0].keys():
            # Check if values in this column are numeric
            numeric_count = 0
            total_count = 0
            
            for row in data[:10]:  # Check first 10 rows
                value = row.get(column)
                if value is not None:
                    total_count += 1
                    try:
                        float(str(value).replace(',', '').replace('$', '').replace('%', ''))
                        numeric_count += 1
                    except:
                        pass
            
            if total_count > 0 and numeric_count / total_count > 0.7:  # 70% numeric
                numeric_columns.append(column)
        
        return numeric_columns
    
    def _generate_chart_title(self, query: str, chart_type: str) -> str:
        """Generate appropriate chart title"""
        # Extract key terms from query
        words = query.split()
        key_words = [word for word in words if len(word) > 3 and word.lower() not in 
                    ['what', 'show', 'tell', 'about', 'the', 'are', 'how', 'can', 'you']]
        
        if key_words:
            title = f"{chart_type.title()} Chart: {' '.join(key_words[:4])}"
        else:
            title = f"{chart_type.title()} Chart"
        
        return title
    
    async def _create_chart(
        self, 
        data: List[Dict[str, Any]], 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create chart based on configuration"""
        if not data:
            return {}
        
        try:
            df = pd.DataFrame(data)
            chart_type = config.get("chart_type", "bar")
            
            if chart_type in self.chart_types:
                fig = self.chart_types[chart_type](df, config)
            else:
                fig = self._create_bar_chart(df, config)
            
            # Convert to JSON for frontend
            return {
                "plotly_json": fig.to_json(),
                "config": config
            }
            
        except Exception as e:
            logger.error(f"Error creating chart: {str(e)}")
            return {}
    
    def _create_line_chart(self, df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """Create line chart"""
        x_col = config.get("x_axis")
        y_col = config.get("y_axis")
        
        if x_col and y_col and x_col in df.columns and y_col in df.columns:
            fig = px.line(df, x=x_col, y=y_col, title=config.get("title", "Line Chart"))
        else:
            # Fallback: use first two columns
            cols = df.columns.tolist()
            if len(cols) >= 2:
                fig = px.line(df, x=cols[0], y=cols[1], title=config.get("title", "Line Chart"))
            else:
                fig = go.Figure()
        
        return fig
    
    def _create_bar_chart(self, df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """Create bar chart"""
        x_col = config.get("x_axis")
        y_col = config.get("y_axis")
        
        if x_col and y_col and x_col in df.columns and y_col in df.columns:
            fig = px.bar(df, x=x_col, y=y_col, title=config.get("title", "Bar Chart"))
        else:
            # Fallback: use first two columns
            cols = df.columns.tolist()
            if len(cols) >= 2:
                fig = px.bar(df, x=cols[0], y=cols[1], title=config.get("title", "Bar Chart"))
            else:
                fig = go.Figure()
        
        return fig
    
    def _create_pie_chart(self, df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """Create pie chart"""
        x_col = config.get("x_axis")
        y_col = config.get("y_axis")
        
        if x_col and y_col and x_col in df.columns and y_col in df.columns:
            fig = px.pie(df, names=x_col, values=y_col, title=config.get("title", "Pie Chart"))
        else:
            # Fallback: use first two columns
            cols = df.columns.tolist()
            if len(cols) >= 2:
                fig = px.pie(df, names=cols[0], values=cols[1], title=config.get("title", "Pie Chart"))
            else:
                fig = go.Figure()
        
        return fig
    
    def _create_scatter_chart(self, df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """Create scatter plot"""
        x_col = config.get("x_axis")
        y_col = config.get("y_axis")
        
        if x_col and y_col and x_col in df.columns and y_col in df.columns:
            fig = px.scatter(df, x=x_col, y=y_col, title=config.get("title", "Scatter Plot"))
        else:
            # Fallback: use first two columns
            cols = df.columns.tolist()
            if len(cols) >= 2:
                fig = px.scatter(df, x=cols[0], y=cols[1], title=config.get("title", "Scatter Plot"))
            else:
                fig = go.Figure()
        
        return fig
    
    def _create_histogram(self, df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """Create histogram"""
        y_col = config.get("y_axis") or config.get("x_axis")
        
        if y_col and y_col in df.columns:
            fig = px.histogram(df, x=y_col, title=config.get("title", "Histogram"))
        else:
            # Fallback: use first numeric column
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            if numeric_cols:
                fig = px.histogram(df, x=numeric_cols[0], title=config.get("title", "Histogram"))
            else:
                fig = go.Figure()
        
        return fig
    
    def _get_data_summary(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get summary statistics of the data"""
        if not data:
            return {}
        
        df = pd.DataFrame(data)
        
        return {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": df.columns.tolist(),
            "numeric_columns": df.select_dtypes(include=['number']).columns.tolist()
        }