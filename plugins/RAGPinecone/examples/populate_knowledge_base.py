import os
import logging
import tempfile
import requests
import re
from dotenv import load_dotenv
import gdown

from rag_pinecone_gamesdk.populate_rag import RAGPopulator
from rag_pinecone_gamesdk import DEFAULT_INDEX_NAME, DEFAULT_NAMESPACE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def download_from_google_drive(folder_url, download_folder):
    """
    Download all files from a Google Drive folder
    
    Args:
        folder_url: URL of the Google Drive folder
        download_folder: Local folder to download files to
        
    Returns:
        List of downloaded file paths
    """
    logger.info(f"Downloading files from Google Drive folder: {folder_url}")
    
    # Extract folder ID from URL
    folder_id_match = re.search(r'folders/([a-zA-Z0-9_-]+)', folder_url)
    if not folder_id_match:
        logger.error(f"Could not extract folder ID from URL: {folder_url}")
        return []
    
    folder_id = folder_id_match.group(1)
    logger.info(f"Folder ID: {folder_id}")
    
    # Create download folder if it doesn't exist
    os.makedirs(download_folder, exist_ok=True)
    
    # Download all files in the folder
    try:
        # Use gdown to download all files in the folder
        downloaded_files = gdown.download_folder(
            id=folder_id,
            output=download_folder,
            quiet=False,
            use_cookies=False
        )
        
        if not downloaded_files:
            logger.warning("No files were downloaded from Google Drive")
            return []
        
        logger.info(f"Downloaded {len(downloaded_files)} files from Google Drive")
        return downloaded_files
    
    except Exception as e:
        logger.error(f"Error downloading files from Google Drive: {str(e)}")
        return []

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
    
    # Google Drive folder URL
    google_drive_url = "https://drive.google.com/drive/folders/1dKYDQxenDkthF0MPr-KOsdPNqEmrAq1c?usp=sharing"
    
    # Create a temporary directory for downloaded files
    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info(f"Created temporary directory for downloaded files: {temp_dir}")
        
        # Download files from Google Drive
        downloaded_files = download_from_google_drive(google_drive_url, temp_dir)
        
        if not downloaded_files:
            logger.error("No files were downloaded from Google Drive. Exiting.")
            return
        
        # Get the Documents folder path for local processing
        documents_folder = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "Documents"
        )
        
        # Ensure the Documents folder exists
        if not os.path.exists(documents_folder):
            os.makedirs(documents_folder)
            logger.info(f"Created Documents folder at: {documents_folder}")
        
        # Initialize the RAGPopulator
        logger.info("Initializing RAGPopulator...")
        populator = RAGPopulator(
            pinecone_api_key=pinecone_api_key,
            openai_api_key=openai_api_key,
            index_name=DEFAULT_INDEX_NAME,
            namespace=DEFAULT_NAMESPACE,
            documents_folder=temp_dir,  # Use the temp directory with downloaded files
        )
        
        # Process all documents in the temporary folder
        logger.info(f"Processing downloaded documents from: {temp_dir}")
        status, message, results = populator.process_documents_folder()
        
        # Log the results
        logger.info(f"Status: {status}")
        logger.info(f"Message: {message}")
        logger.info(f"Processed {results.get('total_files', 0)} files, {results.get('successful_files', 0)} successful")
        
        # Get all document IDs
        ids = populator.fetch_all_ids()
        logger.info(f"Total vectors in database: {len(ids)}")
        
        # Print detailed results for each file
        if 'results' in results:
            logger.info("\nDetailed results:")
            for result in results['results']:
                file_path = result.get('file_path', 'Unknown file')
                status = result.get('status', 'Unknown status')
                message = result.get('message', 'No message')
                logger.info(f"File: {os.path.basename(file_path)}")
                logger.info(f"Status: {status}")
                logger.info(f"Message: {message}")
                logger.info("---")

if __name__ == "__main__":
    main()
