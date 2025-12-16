from app.vectorstore import add_documents
from app.utils import load_text, chunk_text
import logging

logger = logging.getLogger(__name__)

def ingest_document(file_bytes: bytes, filename: str, session_id: str = None):
    from app.progress import progress_tracker
    
    logger.info(f"[PROCESS] Starting document ingestion: {filename}")
    if session_id:
        progress_tracker.add_step(session_id, f"[PROCESS] Processing document: {filename}", "info")
    
    logger.info("[read] Step 1: Loading text from document...")
    if session_id:
        progress_tracker.add_step(session_id, "[read] Extracting text from PDF...", "info")
    
    try:
        text = load_text(file_bytes, filename)
        logger.info(f"✅ Text loaded successfully: {len(text)} characters")
        if session_id:
            progress_tracker.add_step(session_id, f"[OK] Text extracted: {len(text)} characters", "success")
    except Exception as e:
        logger.error(f"❌ Text loading failed: {e}")
        if session_id:
            progress_tracker.add_step(session_id, "[ERROR] Text extraction failed", "error", str(e))
        raise RuntimeError(f"Failed to load text from {filename}: {e}") from e
    
    logger.info("[CHUNK] Step 2: Chunking text into segments...")
    if session_id:
        progress_tracker.add_step(session_id, "[CHUNK] Splitting text into chunks...", "info")
    
    try:
        chunks = chunk_text(text)
        logger.info(f"✅ Text chunked successfully: {len(chunks)} chunks")
        if session_id:
            progress_tracker.add_step(session_id, f"[OK] Created {len(chunks)} text chunks", "success")
        
        for i, chunk in enumerate(chunks[:3]):  # Log first 3 chunks as preview
            logger.info(f"Chunk {i+1} preview: {chunk[:100]}...")
    except Exception as e:
        logger.error(f"❌ Text chunking failed: {e}")
        if session_id:
            progress_tracker.add_step(session_id, "[ERROR] Text chunking failed", "error", str(e))
        raise RuntimeError(f"Failed to chunk text from {filename}: {e}") from e
    
    logger.info("[DATA] Step 3: Adding documents to vector store...")
    if session_id:
        progress_tracker.add_step(session_id, "[DATA] Creating embeddings and storing...", "info")
    
    try:
        add_documents(chunks, source=filename)
        logger.info(f"✅ Document ingestion completed for {filename}")
        if session_id:
            progress_tracker.add_step(session_id, f"[OK] Document stored successfully", "success")
    except Exception as e:
        logger.error(f"❌ Vector store addition failed: {e}")
        if session_id:
            progress_tracker.add_step(session_id, "[ERROR] Vector storage failed", "error", str(e))
        raise RuntimeError(f"Failed to add {filename} to vector store: {e}") from e
