from fastapi import FastAPI
from langserve import add_routes
from langchain.schema.runnable import RunnableLambda
from langchain_server.chains.multimodal_chain import MultimodalRAGChain
from langchain_server.graphs.rag_graph import MultimodalRAGGraph
import asyncio
import logging

logger = logging.getLogger(__name__)

def create_langserve_app() -> FastAPI:
    """Create LangServe application"""
    app = FastAPI(
        title="Multimodal PDF RAG - LangServe",
        description="LangChain server for multimodal PDF analysis",
        version="1.0.0"
    )
    
    # Initialize services
    rag_graph = MultimodalRAGGraph()
    multimodal_chain = MultimodalRAGChain()
    
    # Create runnable for the RAG graph
    async def process_query_runnable(query_dict):
        """Runnable wrapper for RAG graph"""
        query = query_dict.get("query", "")
        if not query:
            return {"error": "No query provided"}
        
        try:
            result = await rag_graph.process_query(query)
            return result
        except Exception as e:
            logger.error(f"Error in RAG processing: {str(e)}")
            return {"error": str(e)}
    
    # Create runnable for multimodal chain
    async def multimodal_chain_runnable(input_dict):
        """Runnable wrapper for multimodal chain"""
        try:
            result = await multimodal_chain.invoke(input_dict)
            return result
        except Exception as e:
            logger.error(f"Error in multimodal chain: {str(e)}")
            return {"error": str(e)}
    
    # Add routes
    add_routes(
        app,
        RunnableLambda(process_query_runnable),
        path="/rag"
    )
    
    add_routes(
        app,
        RunnableLambda(multimodal_chain_runnable),
        path="/multimodal"
    )
    
    return app

# Create the app
langserve_app = create_langserve_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:langserve_app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )