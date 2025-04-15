from typing import Tuple, Dict, Any, Optional

from game_sdk.game.custom_types import Function, FunctionResultStatus, Argument
from rag_pinecone_gamesdk.rag_pinecone_plugin import RAGPineconePlugin
from rag_pinecone_gamesdk.search_rag import RAGSearcher


def query_knowledge_executable(rag_plugin: RAGPineconePlugin, query: str, num_results: int = 3) -> Tuple[FunctionResultStatus, str, Dict[str, Any]]:
    """
    Execute the query_knowledge function from the RAG plugin.
    
    Args:
        rag_plugin: The RAGPineconePlugin instance
        query: The query to search for
        num_results: Number of relevant documents to retrieve
        
    Returns:
        Tuple containing status, message, and results dictionary
    """
    try:
        status, message, results = rag_plugin.query_knowledge(query, num_results)
        
        # Format the results for better readability in chat
        formatted_results = []
        for i, result in enumerate(results.get("results", [])):
            content = result.get("content", "")
            metadata = result.get("metadata", {})
            
            # Format metadata for display
            metadata_str = ", ".join([f"{k}: {v}" for k, v in metadata.items() 
                                     if k not in ["chunk_id", "file_fingerprint"]])
            
            formatted_results.append(f"Document {i+1}:\n{content}\n\nSource: {metadata_str}\n")
        
        formatted_message = f"Found {len(formatted_results)} relevant documents for query: '{query}'\n\n"
        formatted_message += "\n---\n".join(formatted_results)
        
        return FunctionResultStatus.DONE, formatted_message, results
    except Exception as e:
        return FunctionResultStatus.FAILED, f"Error querying knowledge base: {str(e)}", {"query": query}


def query_knowledge_fn(rag_plugin: RAGPineconePlugin) -> Function:
    """
    Create a GAME Function for querying the knowledge base.
    
    Args:
        rag_plugin: The RAGPineconePlugin instance
        
    Returns:
        Function object for the query_knowledge function
    """
    return Function(
        fn_name="query_knowledge",
        fn_description="Query the RAG knowledge base for relevant context",
        args=[
            Argument(name="query", description="The query to find relevant context for", type="str"),
            Argument(name="num_results", description="Number of relevant documents to retrieve (default: 3)", type="int", optional=True),
        ],
        executable=lambda query, num_results=3: query_knowledge_executable(rag_plugin, query, num_results),
    )


def add_document_executable(rag_plugin: RAGPineconePlugin, content: str, metadata: Optional[Dict[str, Any]] = None) -> Tuple[FunctionResultStatus, str, Dict[str, Any]]:
    """
    Execute the add_document function from the RAG plugin.
    
    Args:
        rag_plugin: The RAGPineconePlugin instance
        content: The text content to add
        metadata: Optional metadata about the document
        
    Returns:
        Tuple containing status, message, and results dictionary
    """
    try:
        status, message, results = rag_plugin.add_document(content, metadata)
        return status, message, results
    except Exception as e:
        return FunctionResultStatus.FAILED, f"Error adding document: {str(e)}", {"content": content[:100] + "..." if len(content) > 100 else content}


def add_document_fn(rag_plugin: RAGPineconePlugin) -> Function:
    """
    Create a GAME Function for adding a document to the knowledge base.
    
    Args:
        rag_plugin: The RAGPineconePlugin instance
        
    Returns:
        Function object for the add_document function
    """
    return Function(
        fn_name="add_document",
        fn_description="Add a document to the RAG knowledge base",
        args=[
            Argument(name="content", description="The text content to add to the knowledge base", type="str"),
            Argument(name="metadata", description="Optional metadata about the document", type="dict", optional=True),
        ],
        executable=lambda content, metadata=None: add_document_executable(rag_plugin, content, metadata),
    )


# Advanced RAG search functions

def advanced_query_knowledge_executable(searcher: RAGSearcher, query: str) -> Tuple[FunctionResultStatus, str, Dict[str, Any]]:
    """
    Execute the advanced query_knowledge function using the hybrid retriever.
    
    Args:
        searcher: The RAGSearcher instance
        query: The query to search for
        
    Returns:
        Tuple containing status, message, and results dictionary
    """
    return searcher.query(query)


def advanced_query_knowledge_fn(searcher: RAGSearcher) -> Function:
    """
    Create a GAME Function for advanced querying of the knowledge base.
    
    Args:
        searcher: The RAGSearcher instance
        
    Returns:
        Function object for the advanced_query_knowledge function
    """
    return Function(
        fn_name="advanced_query_knowledge",
        fn_description="Query the RAG knowledge base using hybrid retrieval (vector + BM25) and get an AI-generated answer",
        args=[
            Argument(name="query", description="The query to search for", type="str"),
        ],
        executable=lambda query: advanced_query_knowledge_executable(searcher, query),
    )


def get_relevant_documents_executable(searcher: RAGSearcher, query: str) -> Tuple[FunctionResultStatus, str, Dict[str, Any]]:
    """
    Execute the get_relevant_documents function.
    
    Args:
        searcher: The RAGSearcher instance
        query: The query to search for
        
    Returns:
        Tuple containing status, message, and results dictionary
    """
    return searcher.get_relevant_documents(query)


def get_relevant_documents_fn(searcher: RAGSearcher) -> Function:
    """
    Create a GAME Function for getting relevant documents.
    
    Args:
        searcher: The RAGSearcher instance
        
    Returns:
        Function object for the get_relevant_documents function
    """
    return Function(
        fn_name="get_relevant_documents",
        fn_description="Get relevant documents from the RAG knowledge base using hybrid retrieval (vector + BM25)",
        args=[
            Argument(name="query", description="The query to search for", type="str"),
        ],
        executable=lambda query: get_relevant_documents_executable(searcher, query),
    )
