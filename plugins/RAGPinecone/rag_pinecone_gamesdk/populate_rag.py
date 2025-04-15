import os
import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import hashlib
import glob
import pathlib

from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader,
    CSVLoader,
    UnstructuredMarkdownLoader,
    UnstructuredHTMLLoader,
)

from game_sdk.game.custom_types import Function, FunctionResultStatus, Argument
from rag_pinecone_gamesdk import DEFAULT_INDEX_NAME, DEFAULT_NAMESPACE, DEFAULT_EMBEDDING_MODEL

logger = logging.getLogger(__name__)

class RAGPopulator:
    """
    Utility class for populating the RAG knowledge base with documents.
    """
    
    def __init__(
        self,
        pinecone_api_key: Optional[str] = os.environ.get("PINECONE_API_KEY"),
        openai_api_key: Optional[str] = os.environ.get("OPENAI_API_KEY"),
        index_name: str = DEFAULT_INDEX_NAME,
        namespace: str = DEFAULT_NAMESPACE,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
        documents_folder: Optional[str] = None,
    ):
        self.pinecone_api_key = pinecone_api_key
        self.openai_api_key = openai_api_key
        self.index_name = index_name
        self.namespace = namespace
        self.embedding_model = embedding_model
        
        # Set documents folder path
        if documents_folder is None:
            # Default to Documents folder in the plugin directory
            self.documents_folder = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "Documents"
            )
        else:
            self.documents_folder = documents_folder
        
        # Ensure the documents folder exists
        os.makedirs(self.documents_folder, exist_ok=True)
        
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
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        # File type to loader mapping
        self.file_loaders = {
            ".txt": TextLoader,
            ".pdf": PyPDFLoader,
            ".docx": Docx2txtLoader,
            ".doc": Docx2txtLoader,
            ".csv": CSVLoader,
            ".md": UnstructuredMarkdownLoader,
            ".html": UnstructuredHTMLLoader,
            ".htm": UnstructuredHTMLLoader,
        }
    
    def chunk_document(self, content: str, metadata: Dict[str, Any]) -> List[Document]:
        """
        Split a document into chunks for embedding.
        
        Args:
            content: The document content
            metadata: Metadata for the document
            
        Returns:
            List of Document objects
        """
        # Split text into chunks
        texts = self.text_splitter.split_text(content)
        
        # Create documents with metadata
        documents = []
        for i, chunk in enumerate(texts):
            # Create a unique chunk ID
            chunk_id = f"{metadata.get('doc_id', 'doc')}_{i}"
            
            # Create chunk metadata
            chunk_metadata = metadata.copy()
            chunk_metadata["chunk_id"] = chunk_id
            chunk_metadata["chunk_index"] = i
            chunk_metadata["total_chunks"] = len(texts)
            chunk_metadata["last_updated"] = datetime.now(timezone.utc).isoformat()
            
            # Create document
            doc = Document(
                page_content=chunk,
                metadata=chunk_metadata
            )
            documents.append(doc)
        
        return documents
    
    def add_document(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Tuple[FunctionResultStatus, str, Dict[str, Any]]:
        """
        Add a document to the knowledge base.
        
        Args:
            content: The document content
            metadata: Metadata for the document
            
        Returns:
            Tuple containing status, message, and results dictionary
        """
        try:
            # Initialize metadata if None
            metadata = metadata or {}
            
            # Generate a document ID if not provided
            if "doc_id" not in metadata:
                doc_hash = hashlib.md5(content.encode()).hexdigest()
                metadata["doc_id"] = f"doc_{doc_hash}"
            
            # Add timestamp if not provided
            if "timestamp" not in metadata:
                metadata["timestamp"] = datetime.now(timezone.utc).isoformat()
            
            # Chunk the document
            chunked_docs = self.chunk_document(content, metadata)
            
            # Generate IDs for each chunk
            chunk_ids = [doc.metadata["chunk_id"] for doc in chunked_docs]
            
            # Add documents to vector store
            self.vector_store.add_documents(chunked_docs, ids=chunk_ids)
            
            return (
                FunctionResultStatus.DONE,
                f"Document added successfully with {len(chunked_docs)} chunks",
                {
                    "doc_id": metadata["doc_id"],
                    "num_chunks": len(chunked_docs),
                    "metadata": metadata
                }
            )
        except Exception as e:
            logger.error(f"Error adding document: {str(e)}")
            return (
                FunctionResultStatus.FAILED,
                f"Error adding document: {str(e)}",
                {
                    "content_preview": content[:100] + "..." if len(content) > 100 else content
                }
            )
    
    def add_file(self, file_path: str) -> Tuple[FunctionResultStatus, str, Dict[str, Any]]:
        """
        Add a file to the knowledge base.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple containing status, message, and results dictionary
        """
        try:
            # Get file extension
            file_ext = os.path.splitext(file_path)[1].lower()
            
            # Check if file type is supported
            if file_ext not in self.file_loaders:
                return (
                    FunctionResultStatus.FAILED,
                    f"Unsupported file type: {file_ext}",
                    {"file_path": file_path}
                )
            
            # Get appropriate loader
            loader_class = self.file_loaders[file_ext]
            
            # Load the document
            loader = loader_class(file_path)
            documents = loader.load()
            
            # Get file metadata
            file_stats = os.stat(file_path)
            file_name = os.path.basename(file_path)
            
            # Process each document
            total_chunks = 0
            doc_ids = []
            
            for doc in documents:
                # Create metadata
                metadata = {
                    "source": file_path,
                    "filename": file_name,
                    "filetype": file_ext,
                    "file_size": file_stats.st_size,
                    "created_at": datetime.fromtimestamp(file_stats.st_ctime, tz=timezone.utc).isoformat(),
                    "modified_at": datetime.fromtimestamp(file_stats.st_mtime, tz=timezone.utc).isoformat(),
                }
                
                # Add document
                status, _, results = self.add_document(doc.page_content, metadata)
                
                if status == FunctionResultStatus.DONE:
                    total_chunks += results.get("num_chunks", 0)
                    doc_ids.append(results.get("doc_id"))
            
            return (
                FunctionResultStatus.DONE,
                f"File '{file_name}' added successfully with {total_chunks} chunks",
                {
                    "file_path": file_path,
                    "doc_ids": doc_ids,
                    "total_chunks": total_chunks
                }
            )
        except Exception as e:
            logger.error(f"Error adding file: {str(e)}")
            return (
                FunctionResultStatus.FAILED,
                f"Error adding file: {str(e)}",
                {"file_path": file_path}
            )
    
    def process_documents_folder(self) -> Tuple[FunctionResultStatus, str, Dict[str, Any]]:
        """
        Process all documents in the documents folder.
        
        Returns:
            Tuple containing status, message, and results dictionary
        """
        try:
            # Get all files in the documents folder
            all_files = []
            for ext in self.file_loaders.keys():
                pattern = os.path.join(self.documents_folder, f"**/*{ext}")
                all_files.extend(glob.glob(pattern, recursive=True))
            
            if not all_files:
                return (
                    FunctionResultStatus.DONE,
                    f"No supported files found in {self.documents_folder}",
                    {"documents_folder": self.documents_folder}
                )
            
            # Process each file
            results = []
            for file_path in all_files:
                logger.info(f"Processing file: {file_path}")
                status, message, result = self.add_file(file_path)
                results.append({
                    "file_path": file_path,
                    "status": status,
                    "message": message,
                    "result": result
                })
                logger.info(message)
            
            # Count successful files
            successful_files = sum(1 for r in results if r["status"] == FunctionResultStatus.DONE)
            
            return (
                FunctionResultStatus.DONE,
                f"Processed {len(results)} files, {successful_files} successful",
                {
                    "documents_folder": self.documents_folder,
                    "total_files": len(results),
                    "successful_files": successful_files,
                    "results": results
                }
            )
        except Exception as e:
            logger.error(f"Error processing documents folder: {str(e)}")
            return (
                FunctionResultStatus.FAILED,
                f"Error processing documents folder: {str(e)}",
                {"documents_folder": self.documents_folder}
            )
    
    def delete_document(self, doc_id: str) -> Tuple[FunctionResultStatus, str, Dict[str, Any]]:
        """
        Delete a document from the knowledge base.
        
        Args:
            doc_id: The document ID to delete
            
        Returns:
            Tuple containing status, message, and results dictionary
        """
        try:
            # Fetch documents with the given doc_id
            filter_criteria = {"doc_id": doc_id}
            matching_docs = self.vector_store.similarity_search(
                query="",
                k=1000,
                filter=filter_criteria,
                namespace=self.namespace
            )
            
            # Extract chunk IDs
            chunk_ids = [doc.metadata["chunk_id"] for doc in matching_docs if "chunk_id" in doc.metadata]
            
            if not chunk_ids:
                return (
                    FunctionResultStatus.FAILED,
                    f"No chunks found for document ID: {doc_id}",
                    {"doc_id": doc_id}
                )
            
            # Delete chunks
            self.vector_store.delete(ids=chunk_ids)
            
            return (
                FunctionResultStatus.DONE,
                f"Document deleted successfully. Removed {len(chunk_ids)} chunks.",
                {
                    "doc_id": doc_id,
                    "num_chunks_deleted": len(chunk_ids)
                }
            )
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return (
                FunctionResultStatus.FAILED,
                f"Error deleting document: {str(e)}",
                {"doc_id": doc_id}
            )
    
    def get_document_count(self) -> Tuple[FunctionResultStatus, str, Dict[str, Any]]:
        """
        Get the number of documents in the knowledge base.
        
        Returns:
            Tuple containing status, message, and results dictionary
        """
        try:
            # This is a simplified approach - in a real implementation,
            # you would need to query Pinecone for the actual count
            # For now, we'll just return a placeholder
            return (
                FunctionResultStatus.DONE,
                "Document count retrieved successfully",
                {
                    "count": "Unknown - Pinecone doesn't provide a direct count API. Use fetch_all_ids to get IDs."
                }
            )
        except Exception as e:
            logger.error(f"Error getting document count: {str(e)}")
            return (
                FunctionResultStatus.FAILED,
                f"Error getting document count: {str(e)}",
                {}
            )
    
    def fetch_all_ids(self) -> List[str]:
        """
        Fetch all document IDs from the knowledge base.
        
        Returns:
            List of document IDs
        """
        index = self.pc.Index(self.index_name)
        ids = []
        for id_batch in index.list(namespace=self.namespace):
            ids.extend(id_batch)
        return ids


# Function wrappers for GAME SDK integration

def process_documents_folder_executable(populator: RAGPopulator) -> Tuple[FunctionResultStatus, str, Dict[str, Any]]:
    """
    Execute the process_documents_folder function.
    
    Args:
        populator: The RAGPopulator instance
        
    Returns:
        Tuple containing status, message, and results dictionary
    """
    return populator.process_documents_folder()


def process_documents_folder_fn(populator: RAGPopulator) -> Function:
    """
    Create a GAME Function for processing the documents folder.
    
    Args:
        populator: The RAGPopulator instance
        
    Returns:
        Function object
    """
    return Function(
        fn_name="process_documents_folder",
        fn_description="Process all documents in the documents folder and add them to the knowledge base",
        args=[],
        executable=lambda: process_documents_folder_executable(populator),
    )


def add_document_executable(populator: RAGPopulator, content: str, metadata: Optional[Dict[str, Any]] = None) -> Tuple[FunctionResultStatus, str, Dict[str, Any]]:
    """
    Execute the add_document function.
    
    Args:
        populator: The RAGPopulator instance
        content: The document content
        metadata: Metadata for the document
        
    Returns:
        Tuple containing status, message, and results dictionary
    """
    return populator.add_document(content, metadata)


def add_document_fn(populator: RAGPopulator) -> Function:
    """
    Create a GAME Function for adding a document.
    
    Args:
        populator: The RAGPopulator instance
        
    Returns:
        Function object
    """
    return Function(
        fn_name="add_document",
        fn_description="Add a document to the RAG knowledge base",
        args=[
            Argument(name="content", description="The document content", type="str"),
            Argument(name="metadata", description="Metadata for the document", type="dict", optional=True),
        ],
        executable=lambda content, metadata=None: add_document_executable(populator, content, metadata),
    )


def add_file_executable(populator: RAGPopulator, file_path: str) -> Tuple[FunctionResultStatus, str, Dict[str, Any]]:
    """
    Execute the add_file function.
    
    Args:
        populator: The RAGPopulator instance
        file_path: Path to the file
        
    Returns:
        Tuple containing status, message, and results dictionary
    """
    return populator.add_file(file_path)


def add_file_fn(populator: RAGPopulator) -> Function:
    """
    Create a GAME Function for adding a file.
    
    Args:
        populator: The RAGPopulator instance
        
    Returns:
        Function object
    """
    return Function(
        fn_name="add_file",
        fn_description="Add a file to the RAG knowledge base",
        args=[
            Argument(name="file_path", description="Path to the file", type="str"),
        ],
        executable=lambda file_path: add_file_executable(populator, file_path),
    )


def delete_document_executable(populator: RAGPopulator, doc_id: str) -> Tuple[FunctionResultStatus, str, Dict[str, Any]]:
    """
    Execute the delete_document function.
    
    Args:
        populator: The RAGPopulator instance
        doc_id: The document ID to delete
        
    Returns:
        Tuple containing status, message, and results dictionary
    """
    return populator.delete_document(doc_id)


def delete_document_fn(populator: RAGPopulator) -> Function:
    """
    Create a GAME Function for deleting a document.
    
    Args:
        populator: The RAGPopulator instance
        
    Returns:
        Function object
    """
    return Function(
        fn_name="delete_document",
        fn_description="Delete a document from the RAG knowledge base",
        args=[
            Argument(name="doc_id", description="The document ID to delete", type="str"),
        ],
        executable=lambda doc_id: delete_document_executable(populator, doc_id),
    )


# Example usage
if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Initialize populator
    populator = RAGPopulator()
    
    # Process all documents in the Documents folder
    print("Processing documents folder...")
    status, message, results = populator.process_documents_folder()
    print(f"Status: {status}")
    print(f"Message: {message}")
    print(f"Processed {results.get('total_files', 0)} files, {results.get('successful_files', 0)} successful")
    
    # Get all document IDs
    ids = populator.fetch_all_ids()
    print(f"Total vectors in database: {len(ids)}")
