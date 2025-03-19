# RAGPinecone Plugin for GAME SDK

A Retrieval Augmented Generation (RAG) plugin using Pinecone as the vector database for the GAME SDK.

## Features

- Query a knowledge base for relevant context
- Advanced hybrid search (vector + BM25) for better retrieval
- AI-generated answers based on retrieved documents
- Add documents to the knowledge base
- Delete documents from the knowledge base
- Chunk documents for better retrieval
- Process documents from a folder automatically
- Integrate with Telegram bot for RAG-powered conversations

## Installation

### From Source

1. Clone the repository or navigate to the plugin directory:
```bash
cd game-python/plugins/RAGPinecone
```

2. Install the plugin in development mode:
```bash
pip install -e .
```

This will install all required dependencies and make the plugin available in your environment.

## Setup and Configuration

1. Set the following environment variables:
   - `PINECONE_API_KEY`: Your Pinecone API key
   - `OPENAI_API_KEY`: Your OpenAI API key (for embeddings)
   - `GAME_API_KEY`: Your GAME API key
   - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token (if using with Telegram)

2. Import and initialize the plugin to use in your agent:

```python
from rag_pinecone_gamesdk.rag_pinecone_plugin import RAGPineconePlugin
from rag_pinecone_gamesdk.rag_pinecone_game_functions import query_knowledge_fn, add_document_fn

# Initialize the plugin
rag_plugin = RAGPineconePlugin(
    pinecone_api_key="your-pinecone-api-key",
    openai_api_key="your-openai-api-key",
    index_name="your-index-name",
    namespace="your-namespace"
)

# Add the functions to your agent's action space
agent_action_space = [
    query_knowledge_fn(rag_plugin),
    add_document_fn(rag_plugin),
    # ... other functions
]
```

## Available Functions

### Basic RAG Functions

1. `query_knowledge(query: str, num_results: int = 3)` - Query the knowledge base for relevant context
2. `add_document(content: str, metadata: dict = None)` - Add a document to the knowledge base

### Advanced RAG Functions

1. `advanced_query_knowledge(query: str)` - Query the knowledge base using hybrid retrieval (vector + BM25) and get an AI-generated answer
2. `get_relevant_documents(query: str)` - Get relevant documents using hybrid retrieval without generating an answer

Example usage of advanced functions:

```python
from rag_pinecone_gamesdk.search_rag import RAGSearcher
from rag_pinecone_gamesdk.rag_pinecone_game_functions import advanced_query_knowledge_fn, get_relevant_documents_fn

# Initialize the RAG searcher
rag_searcher = RAGSearcher(
    pinecone_api_key="your-pinecone-api-key",
    openai_api_key="your-openai-api-key",
    index_name="your-index-name",
    namespace="your-namespace"
)

# Add the advanced functions to your agent's action space
agent_action_space = [
    advanced_query_knowledge_fn(rag_searcher),
    get_relevant_documents_fn(rag_searcher),
    # ... other functions
]
```

## Populating the Knowledge Base

### Using the Documents Folder

The easiest way to populate the knowledge base is to place your documents in the `Documents` folder and run the provided script:

```bash
cd game-python/plugins/RAGPinecone
python examples/populate_knowledge_base.py
```

This will process all supported files in the Documents folder and add them to the knowledge base.

Supported file types:
- `.txt` - Text files
- `.pdf` - PDF documents
- `.docx` - Word documents
- `.doc` - Word documents
- `.csv` - CSV files
- `.md` - Markdown files
- `.html` - HTML files

### Using the API

You can also populate the knowledge base programmatically:

```python
from rag_pinecone_gamesdk.populate_rag import RAGPopulator

# Initialize the populator
populator = RAGPopulator(
    pinecone_api_key="your-pinecone-api-key",
    openai_api_key="your-openai-api-key",
    index_name="your-index-name",
    namespace="your-namespace"
)

# Add a document
content = "Your document content here"
metadata = {
    "title": "Document Title",
    "author": "Author Name",
    "source": "Source Name",
}

status, message, results = populator.add_document(content, metadata)
print(f"Status: {status}")
print(f"Message: {message}")
print(f"Results: {results}")

# Process all documents in a folder
status, message, results = populator.process_documents_folder()
print(f"Status: {status}")
print(f"Message: {message}")
print(f"Processed {results.get('total_files', 0)} files, {results.get('successful_files', 0)} successful")
```

## Testing the Advanced Search

You can test the advanced search functionality using the provided example script:

```bash
cd game-python/plugins/RAGPinecone
python examples/test_advanced_search.py
```

This will run a series of test queries using the advanced hybrid retrieval system.

## Integration with Telegram

See the `examples/test_rag_pinecone_telegram.py` file for an example of how to integrate the RAGPinecone plugin with a Telegram bot.

To run the Telegram bot with advanced RAG capabilities:

```bash
cd game-python/plugins/RAGPinecone
python examples/test_rag_pinecone_telegram.py
```

## Advanced Usage

### Hybrid Retrieval

The advanced search functionality uses a hybrid retrieval approach that combines:

1. **Vector Search**: Uses embeddings to find semantically similar documents
2. **BM25 Search**: Uses keyword matching to find documents with relevant terms

This hybrid approach often provides better results than either method alone, especially for complex queries.

### Custom Document Processing

You can customize how documents are processed by extending the `RAGPopulator` class:

```python
from rag_pinecone_gamesdk.populate_rag import RAGPopulator

class CustomRAGPopulator(RAGPopulator):
    def chunk_document(self, content, metadata):
        # Custom chunking logic
        # ...
        return chunked_docs
```

### Custom Embedding Models

You can use different embedding models by specifying the `embedding_model` parameter:

```python
rag_plugin = RAGPineconePlugin(
    embedding_model="sentence-transformers/all-mpnet-base-v2"
)
```

## Requirements

- Python 3.9+
- Pinecone account
- OpenAI API key
- GAME SDK
- langchain
- langchain_community
- langchain_pinecone
- langchain_openai 