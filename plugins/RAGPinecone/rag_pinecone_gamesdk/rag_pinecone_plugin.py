from typing import Dict, List, Optional, Tuple, Any
import os
import logging
from game_sdk.game.custom_types import Function, FunctionResultStatus, Argument
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.schema import Document

from rag_pinecone_gamesdk import DEFAULT_INDEX_NAME, DEFAULT_NAMESPACE, DEFAULT_EMBEDDING_MODEL

logger = logging.getLogger(__name__)

class RAGPineconePlugin:
    """
    RAG (Retrieval Augmented Generation) plugin using Pinecone for vector storage
    
    Requires:
    - Pinecone API key
    - OpenAI API key for embeddings
    
    Example:
        rag_plugin = RAGPineconePlugin(
            pinecone_api_key="your-pinecone-api-key",
            openai_api_key="your-openai-api-key",
            index_name="your-index-name",
        )

        query_knowledge_fn = rag_plugin.get_function("query_knowledge")
    """
    def __init__(
        self,
        pinecone_api_key: Optional[str] = os.environ.get("PINECONE_API_KEY"),
        openai_api_key: Optional[str] = os.environ.get("OPENAI_API_KEY"),
        index_name: str = DEFAULT_INDEX_NAME,
        namespace: str = DEFAULT_NAMESPACE,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    ):
        self.pinecone_api_key = pinecone_api_key
        self.openai_api_key = openai_api_key
        self.index_name = index_name
        self.namespace = namespace
        self.embedding_model = embedding_model
        
        # Initialize Pinecone client
        self.pc = Pinecone(api_key=self.pinecone_api_key)
        
        # Create index if it doesn't exist
        if self.index_name not in self.pc.list_indexes().names():
            logger.info(f"Creating index '{self.index_name}'...")
            self.pc.create_index(
                name=self.index_name,
                dimension=1536,
                metric="dotproduct",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            logger.info("Index created!")
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            model=self.embedding_model,
            openai_api_key=self.openai_api_key
        )
        
        # Initialize vector store
        self.vector_store = PineconeVectorStore.from_existing_index(
            index_name=self.index_name,
            embedding=self.embeddings,
            namespace=self.namespace
        )

        # Available client functions
        self._functions: Dict[str, Function] = {
            "query_knowledge": Function(
                fn_name="query_knowledge",
                fn_description="Query the RAG knowledge base for relevant context",
                args=[
                    Argument(
                        name="query",
                        description="The query to find relevant context for",
                        type="string",
                    ),
                    Argument(
                        name="num_results",
                        description="Number of relevant documents to retrieve",
                        type="int",
                        optional=True
                    ),
                ],
                executable=self.query_knowledge,
            ),
            "add_document": Function(
                fn_name="add_document",
                fn_description="Add a document to the RAG knowledge base",
                args=[
                    Argument(
                        name="content",
                        description="The text content to add to the knowledge base",
                        type="string",
                    ),
                    Argument(
                        name="metadata",
                        description="Optional metadata about the document",
                        type="dict",
                        optional=True
                    ),
                ],
                executable=self.add_document,
            ),
        }

    @property
    def available_functions(self) -> List[str]:
        """Get list of available function names."""
        return list(self._functions.keys())

    def get_function(self, fn_name: str) -> Function:
        """
        Get a specific function by name.

        Args:
            fn_name: Name of the function to retrieve

        Raises:
            ValueError: If function name is not found

        Returns:
            Function object
        """
        if fn_name not in self._functions:
            raise ValueError(
                f"Function '{fn_name}' not found. Available functions: {', '.join(self.available_functions)}"
            )
        return self._functions[fn_name]

    def query_knowledge(self, query: str, num_results: int = 3) -> Tuple[FunctionResultStatus, str, Dict[str, Any]]:
        """
        Query the knowledge base for relevant context.

        Args:
            query: The query to search for
            num_results: Number of relevant documents to retrieve

        Returns:
            Tuple containing status, message, and results dictionary
        """
        try:
            # Perform similarity search
            docs = self.vector_store.similarity_search(
                query=query,
                k=num_results,
                namespace=self.namespace
            )
            
            # Format results
            results = []
            for doc in docs:
                results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata
                })
            
            return (
                FunctionResultStatus.DONE,
                f"Found {len(results)} relevant documents",
                {
                    "query": query,
                    "results": results
                }
            )
        except Exception as e:
            logger.error(f"Error querying knowledge base: {str(e)}")
            return (
                FunctionResultStatus.FAILED,
                f"Error querying knowledge base: {str(e)}",
                {
                    "query": query
                }
            )

    def add_document(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Tuple[FunctionResultStatus, str, Dict[str, Any]]:
        """
        Add a document to the knowledge base.

        Args:
            content: The text content to add
            metadata: Optional metadata about the document

        Returns:
            Tuple containing status, message, and results dictionary
        """
        try:
            # Create document
            metadata = metadata or {}
            doc = Document(
                page_content=content,
                metadata=metadata
            )
            
            # Generate a document ID
            doc_id = f"doc_{metadata.get('id', hash(content))}"
            
            # Add document to vector store
            self.vector_store.add_documents([doc], ids=[doc_id])
            
            return (
                FunctionResultStatus.DONE,
                f"Document added successfully with ID: {doc_id}",
                {
                    "doc_id": doc_id,
                    "metadata": metadata
                }
            )
        except Exception as e:
            logger.error(f"Error adding document: {str(e)}")
            return (
                FunctionResultStatus.FAILED,
                f"Error adding document: {str(e)}",
                {
                    "content": content[:100] + "..." if len(content) > 100 else content
                }
            )
