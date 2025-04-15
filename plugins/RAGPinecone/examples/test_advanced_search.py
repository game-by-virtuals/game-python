import os
import logging
from dotenv import load_dotenv

from rag_pinecone_gamesdk.search_rag import RAGSearcher
from rag_pinecone_gamesdk import DEFAULT_INDEX_NAME, DEFAULT_NAMESPACE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def main():
    # Load environment variables
    load_dotenv()
    
    # Check for required environment variables
    pinecone_api_key = os.environ.get("PINECONE_API_KEY")
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    
    if not pinecone_api_key:
        logger.error("PINECONE_API_KEY environment variable is not set")
        return
    
    if not openai_api_key:
        logger.error("OPENAI_API_KEY environment variable is not set")
        return
    
    # Initialize the RAG searcher
    logger.info("Initializing RAG searcher...")
    searcher = RAGSearcher(
        pinecone_api_key=pinecone_api_key,
        openai_api_key=openai_api_key,
        index_name=DEFAULT_INDEX_NAME,
        namespace=DEFAULT_NAMESPACE,
        llm_model="gpt-4",  # You can change this to "gpt-3.5-turbo" for faster, cheaper responses
        temperature=0.0,
        k=4  # Number of documents to retrieve
    )
    
    # Test queries
    test_queries = [
        "How do I build a custom function?",
        "How can I contribute plugins to the GAME SDK?",
        "How do I deploy my AI application?",
    ]
    
    # Run test queries
    for query in test_queries:
        logger.info(f"\n\n=== Testing query: '{query}' ===")
        
        # Get AI-generated answer with hybrid retrieval
        logger.info("Getting AI-generated answer with hybrid retrieval...")
        status, message, results = searcher.query(query)
        logger.info(f"Status: {status}")
        logger.info(f"Answer: {message}")
        logger.info(f"Source documents: {len(results.get('source_documents', []))}")
        
        # Get relevant documents only
        logger.info("\nGetting relevant documents only...")
        status, message, results = searcher.get_relevant_documents(query)
        logger.info(f"Status: {status}")
        logger.info(f"Found {len(results.get('results', []))} relevant documents")
        
        # Print first document preview
        if results.get('results'):
            first_doc = results['results'][0]
            content_preview = first_doc['content'][:100] + "..." if len(first_doc['content']) > 100 else first_doc['content']
            logger.info(f"First document preview: {content_preview}")

if __name__ == "__main__":
    main()
