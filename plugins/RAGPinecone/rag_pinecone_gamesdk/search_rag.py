import os
import logging
import sys
import warnings
from typing import List, Dict, Any, Optional, Tuple, Type

from langchain.tools import BaseTool
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter, SpacyTextSplitter
from langchain_community.retrievers import BM25Retriever
from langchain.schema import BaseRetriever, Document
from pydantic import Field, BaseModel

from game_sdk.game.custom_types import Function, FunctionResultStatus, Argument
from rag_pinecone_gamesdk import DEFAULT_INDEX_NAME, DEFAULT_NAMESPACE, DEFAULT_EMBEDDING_MODEL

logger = logging.getLogger(__name__)

# Increase the recursion limit for complex document processing
sys.setrecursionlimit(10000)


class HybridRetriever(BaseRetriever):
    """
    A hybrid retriever that combines vector search and BM25 for better results.
    """
    vector_store: Any = Field(default=None)
    bm25_retriever: BM25Retriever = Field(default=None)
    k: int = Field(default=4)

    def _get_relevant_documents(self, query: str, run_manager: Any = None) -> List[Document]:
        """
        Get relevant documents using both vector search and BM25.
        
        Args:
            query: The search query
            run_manager: Optional run manager
            
        Returns:
            List of relevant documents
        """
        # Get documents from vector store
        vector_docs = self.vector_store.similarity_search(query, k=self.k)
        
        # Get documents from BM25
        bm25_docs = self.bm25_retriever.invoke(query)[:self.k]
        
        # Combine and deduplicate
        all_docs = vector_docs + bm25_docs
        seen = set()
        unique_docs = []
        for doc in all_docs:
            if doc.page_content not in seen:
                seen.add(doc.page_content)
                unique_docs.append(doc)
        
        return unique_docs[:self.k]

    def invoke(self, input: str, run_manager: Any = None, **kwargs) -> List[Document]:
        """
        Invoke the retriever.
        
        Args:
            input: The search query
            run_manager: Optional run manager
            
        Returns:
            List of relevant documents
        """
        return self._get_relevant_documents(input, run_manager=run_manager)

    async def ainvoke(self, input: str, run_manager: Any = None, **kwargs) -> List[Document]:
        """
        Asynchronously invoke the retriever.
        
        Args:
            input: The search query
            run_manager: Optional run manager
            
        Returns:
            List of relevant documents
        """
        return self._get_relevant_documents(input, run_manager=run_manager)


class RAGSearcher:
    """
    Advanced RAG searcher with hybrid retrieval capabilities.
    """
    
    def __init__(
        self,
        pinecone_api_key: Optional[str] = os.environ.get("PINECONE_API_KEY"),
        openai_api_key: Optional[str] = os.environ.get("OPENAI_API_KEY"),
        index_name: str = DEFAULT_INDEX_NAME,
        namespace: str = DEFAULT_NAMESPACE,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
        llm_model: str = "gpt-4",
        temperature: float = 0.0,
        k: int = 4,
    ):
        """
        Initialize the RAG searcher.
        
        Args:
            pinecone_api_key: Pinecone API key
            openai_api_key: OpenAI API key
            index_name: Pinecone index name
            namespace: Pinecone namespace
            embedding_model: OpenAI embedding model
            llm_model: LLM model to use for answering
            temperature: Temperature for the LLM
            k: Number of documents to retrieve
        """
        self.pinecone_api_key = pinecone_api_key
        self.openai_api_key = openai_api_key
        self.index_name = index_name
        self.namespace = namespace
        self.embedding_model = embedding_model
        self.llm_model = llm_model
        self.temperature = temperature
        self.k = k
        
        # These will be initialized when needed
        self.llm = None
        self.vector_store = None
        self.bm25_retriever = None
        self.hybrid_retriever = None
        self.qa_chain = None
        
        # Initialize components if API keys are available
        if self.pinecone_api_key and self.openai_api_key:
            self.initialize_components()
    
    def initialize_components(self):
        """
        Initialize the retrieval components.
        """
        try:
            logger.info(f"Initializing RAG components for index: {self.index_name}, namespace: {self.namespace}")
            
            # Initialize LLM
            self.llm = ChatOpenAI(
                api_key=self.openai_api_key,
                model_name=self.llm_model,
                temperature=self.temperature
            )
            
            # Initialize embeddings
            embeddings = OpenAIEmbeddings(
                model=self.embedding_model,
                openai_api_key=self.openai_api_key
            )
            
            # Initialize vector store
            self.vector_store = PineconeVectorStore.from_existing_index(
                index_name=self.index_name,
                namespace=self.namespace,
                embedding=embeddings
            )
            
            # Get all documents for BM25
            all_docs = self.vector_store.similarity_search("", k=1000)  # Get a sample of documents
            logger.info(f"Retrieved {len(all_docs)} documents from vector store for BM25 indexing")
            
            # Initialize text splitter for BM25
            # Suppress specific warnings from SpaCy
            warnings.filterwarnings("ignore", message="\\[W108\\] The rule-based lemmatizer did not find POS annotation for one or more tokens.*")
            
            try:
                text_splitter = SpacyTextSplitter(
                    pipeline="en_core_web_sm",
                    chunk_size=1500,
                    chunk_overlap=200
                )
                split_docs = text_splitter.split_documents(all_docs)
            except Exception as e:
                logger.warning(f"Error using SpacyTextSplitter: {str(e)}. Falling back to RecursiveCharacterTextSplitter.")
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1500,
                    chunk_overlap=200
                )
                split_docs = text_splitter.split_documents(all_docs)
            
            # Initialize BM25 retriever
            self.bm25_retriever = BM25Retriever.from_documents(split_docs)
            logger.info("BM25 retriever initialized successfully")
            
            # Initialize hybrid retriever
            self.hybrid_retriever = HybridRetriever(
                vector_store=self.vector_store,
                bm25_retriever=self.bm25_retriever,
                k=self.k
            )
            
            # Initialize QA chain
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.hybrid_retriever
            )
            
            logger.info("RAG components initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing RAG components: {str(e)}")
            raise
    
    def query(self, query: str) -> Tuple[FunctionResultStatus, str, Dict[str, Any]]:
        """
        Query the knowledge base.
        
        Args:
            query: The query to search for
            
        Returns:
            Tuple containing status, message, and results dictionary
        """
        try:
            # Initialize components if not already initialized
            if not self.qa_chain:
                self.initialize_components()
            
            # Check if components are initialized
            if not self.qa_chain:
                return (
                    FunctionResultStatus.FAILED,
                    "RAG system is not properly initialized. Please check the setup.",
                    {"query": query}
                )
            
            # Get answer from QA chain
            result = self.qa_chain.invoke(query)
            answer = result['result'] if isinstance(result, dict) and 'result' in result else str(result)
            
            # Get source documents
            source_docs = []
            if self.hybrid_retriever:
                docs = self.hybrid_retriever.invoke(query)
                for i, doc in enumerate(docs):
                    source_docs.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata
                    })
            
            return (
                FunctionResultStatus.DONE,
                answer,
                {
                    "query": query,
                    "source_documents": source_docs
                }
            )
        except Exception as e:
            logger.error(f"Error querying knowledge base: {str(e)}")
            return (
                FunctionResultStatus.FAILED,
                f"Error querying knowledge base: {str(e)}",
                {"query": query}
            )
    
    def get_relevant_documents(self, query: str) -> Tuple[FunctionResultStatus, str, Dict[str, Any]]:
        """
        Get relevant documents for a query without generating an answer.
        
        Args:
            query: The query to search for
            
        Returns:
            Tuple containing status, message, and results dictionary
        """
        try:
            # Initialize components if not already initialized
            if not self.hybrid_retriever:
                self.initialize_components()
            
            # Check if components are initialized
            if not self.hybrid_retriever:
                return (
                    FunctionResultStatus.FAILED,
                    "RAG system is not properly initialized. Please check the setup.",
                    {"query": query}
                )
            
            # Get relevant documents
            docs = self.hybrid_retriever.invoke(query)
            
            # Format results
            results = []
            for i, doc in enumerate(docs):
                results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata
                })
            
            # Format message
            formatted_message = f"Found {len(results)} relevant documents for query: '{query}'\n\n"
            for i, result in enumerate(results):
                content = result["content"]
                metadata = result["metadata"]
                
                # Format metadata for display
                metadata_str = ", ".join([f"{k}: {v}" for k, v in metadata.items() 
                                        if k not in ["chunk_id", "file_fingerprint"]])
                
                formatted_message += f"Document {i+1}:\n{content}\n\nSource: {metadata_str}\n\n---\n\n"
            
            return (
                FunctionResultStatus.DONE,
                formatted_message,
                {
                    "query": query,
                    "results": results
                }
            )
        except Exception as e:
            logger.error(f"Error retrieving relevant documents: {str(e)}")
            return (
                FunctionResultStatus.FAILED,
                f"Error retrieving relevant documents: {str(e)}",
                {"query": query}
            )


# Function wrappers for GAME SDK integration

def query_knowledge_executable(searcher: RAGSearcher, query: str) -> Tuple[FunctionResultStatus, str, Dict[str, Any]]:
    """
    Execute the query_knowledge function.
    
    Args:
        searcher: The RAGSearcher instance
        query: The query to search for
        
    Returns:
        Tuple containing status, message, and results dictionary
    """
    return searcher.query(query)


def query_knowledge_fn(searcher: RAGSearcher) -> Function:
    """
    Create a GAME Function for querying the knowledge base.
    
    Args:
        searcher: The RAGSearcher instance
        
    Returns:
        Function object
    """
    return Function(
        fn_name="query_knowledge",
        fn_description="Query the RAG knowledge base for relevant information and get an AI-generated answer",
        args=[
            Argument(name="query", description="The query to search for", type="str"),
        ],
        executable=lambda query: query_knowledge_executable(searcher, query),
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
        Function object
    """
    return Function(
        fn_name="get_relevant_documents",
        fn_description="Get relevant documents from the RAG knowledge base without generating an answer",
        args=[
            Argument(name="query", description="The query to search for", type="str"),
        ],
        executable=lambda query: get_relevant_documents_executable(searcher, query),
    )


# Example usage
if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Initialize searcher
    searcher = RAGSearcher()
    
    # Test query
    query = "What is RAG?"
    print(f"Query: {query}")
    status, message, results = searcher.query(query)
    print(f"Status: {status}")
    print(f"Answer: {message}")
    print(f"Source documents: {len(results.get('source_documents', []))}")
    
    # Test get relevant documents
    print("\nGetting relevant documents...")
    status, message, results = searcher.get_relevant_documents(query)
    print(f"Status: {status}")
    print(f"Found {len(results.get('results', []))} relevant documents") 