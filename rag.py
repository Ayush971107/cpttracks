import os
import csv
import time
import logging
from typing import List, Tuple, Dict, Any
from openai import OpenAI, RateLimitError, APITimeoutError, APIError, APIConnectionError, InternalServerError
from pinecone import Pinecone, ServerlessSpec
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
import dotenv

# Load environment variables
dotenv.load_dotenv()

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('embedding_job.log')
    ]
)
logger = logging.getLogger(__name__)

# Configuration
OPENAI_EMBEDDING_MODEL = "text-embedding-ada-002"
EMBEDDING_DIMENSION = 1536
EMBEDDING_BATCH_SIZE = 100  # Max batch size for OpenAI embeddings
UPSERT_BATCH_SIZE = 100     # Batch size for Pinecone upserts
MAX_RETRIES = 5

# Initialize clients
try:
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    index_name = "insurance-codes"
    
    if not all([os.getenv("OPENAI_API_KEY"), pinecone_api_key]):
        raise ValueError("Missing required API keys. Please set OPENAI_API_KEY and PINECONE_API_KEY environment variables.")
    
    # Initialize Pinecone client
    pc = Pinecone(api_key=pinecone_api_key)
    
    # Create index if it doesn't exist
    if index_name not in pc.list_indexes().names():
        logger.info(f"Creating new index: {index_name}")
        pc.create_index(
            name=index_name,
            dimension=EMBEDDING_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
    
    index = pc.Index(index_name)
    logger.info(f"Connected to Pinecone index: {index_name}")
    
except Exception as e:
    logger.error(f"Initialization failed: {str(e)}")
    raise

# Define tables to process
tables = [
    ("hspcs_codes.csv", "HSPCS Code", "Enhanced Description"),
    ("cpt_codes.csv", "CPT Code", "Enhanced Description"),
    ("icd10pcs_codes.csv", "ICD10PCS_Code", "Enhanced_Description"),
]

@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type((
        RateLimitError,
        APITimeoutError,
        APIError,
        APIConnectionError,
        InternalServerError
    )),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Get embeddings for a batch of texts with retry logic."""
    try:
        response = openai_client.embeddings.create(
            model=OPENAI_EMBEDDING_MODEL,
            input=texts
        )
        return [item.embedding for item in response.data]
    except Exception as e:
        logger.error(f"Error getting embeddings: {str(e)}")
        raise

def process_batch(batch: List[Tuple[str, str]], index) -> None:
    """Process a batch of (id, text) pairs and upsert to Pinecone."""
    if not batch:
        return
    
    ids, texts = zip(*batch)
    
    try:
        # Get embeddings for the batch
        embeddings = get_embeddings_batch(list(texts))
        
        # Prepare vectors for upsert
        vectors = list(zip(ids, embeddings))
        
        # Upsert in chunks to avoid large payloads
        for i in range(0, len(vectors), UPSERT_BATCH_SIZE):
            chunk = vectors[i:i + UPSERT_BATCH_SIZE]
            try:
                index.upsert(vectors=chunk)
                logger.info(f"Upserted batch of {len(chunk)} vectors")
            except Exception as e:
                logger.error(f"Failed to upsert batch {i//UPSERT_BATCH_SIZE}: {str(e)}")
                # Log failed IDs for potential retry
                failed_ids = [id_ for id_, _ in chunk]
                logger.error(f"Failed IDs: {failed_ids}")
                
    except Exception as e:
        logger.error(f"Error processing batch: {str(e)}")
        raise

def process_file(path: str, code_col: str, desc_col: str, index) -> int:
    """Process a single CSV file and return number of processed rows."""
    processed = 0
    batch = []
    
    try:
        with open(path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            total_rows = sum(1 for _ in reader)  # Get total rows for progress tracking
            f.seek(0)  # Reset file pointer
            reader = csv.DictReader(f)  # Recreate reader
            
            logger.info(f"Processing {path} with {total_rows} rows")
            
            for i, row in enumerate(reader, 1):
                try:
                    # Create a unique ID using file basename and code
                    file_prefix = os.path.splitext(os.path.basename(path))[0]
                    code = f"{file_prefix}:{row[code_col]}"
                    text = row[desc_col]
                    
                    batch.append((code, text))
                    
                    # Process batch when it reaches the desired size
                    if len(batch) >= EMBEDDING_BATCH_SIZE:
                        process_batch(batch, index)
                        processed += len(batch)
                        batch = []
                        logger.info(f"Progress: {i}/{total_rows} rows processed ({i/total_rows:.1%})")
                        
                except Exception as e:
                    logger.error(f"Error processing row {i} in {path}: {str(e)}")
                    continue
            
            # Process any remaining items in the last batch
            if batch:
                process_batch(batch, index)
                processed += len(batch)
                
    except Exception as e:
        logger.error(f"Error processing file {path}: {str(e)}")
        raise
    
    return processed

def main():
    total_processed = 0
    start_time = time.time()
    
    try:
        for path, code_col, desc_col in tables:
            if not os.path.exists(path):
                logger.warning(f"File not found, skipping: {path}")
                continue
                
            processed = process_file(path, code_col, desc_col, index)
            total_processed += processed
            logger.info(f"Completed processing {path}: {processed} rows")
        
        elapsed = time.time() - start_time
        logger.info(f"✅ Completed! Processed {total_processed} total rows in {elapsed:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Job failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()  