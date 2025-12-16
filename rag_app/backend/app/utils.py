from PyPDF2 import PdfReader
import io
import logging

logger = logging.getLogger(__name__)

def load_text(file_bytes, filename):
    logger.info(f"[FILE] Loading text from: {filename}")
    
    if filename.lower().endswith(".pdf"):
        logger.info("[PROCESS] Processing PDF file...")
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            logger.info(f"[OK] PDF loaded successfully: {len(reader.pages)} pages")
            
            text_parts = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                text_parts.append(page_text)
                logger.info(f"Page {i+1}: {len(page_text)} characters extracted")
            
            full_text = "\n".join(text_parts)
            logger.info(f"[OK] PDF text extraction completed: {len(full_text)} total characters")
            return full_text
            
        except Exception as e:
            logger.error(f"[ERROR] PDF processing failed: {e}")
            raise RuntimeError(f"Failed to process PDF {filename}: {e}") from e
    else:
        logger.info("[PROCESS] Processing text file...")
        try:
            text = file_bytes.decode("utf-8", errors="ignore")
            logger.info(f"[OK] Text file loaded: {len(text)} characters")
            return text
        except Exception as e:
            logger.error(f"[ERROR] Text file processing failed: {e}")
            raise RuntimeError(f"Failed to process text file {filename}: {e}") from e

def chunk_text(text, size=800, overlap=150):
    logger.info(f"[CHUNK] Chunking text: {len(text)} characters with size={size}, overlap={overlap}")
    
    if not text.strip():
        logger.warning("[WARNING] Empty text provided for chunking")
        return []
    
    chunks = []
    start = 0
    chunk_count = 0
    
    while start < len(text):
        chunk = text[start:start+size]
        chunks.append(chunk)
        chunk_count += 1
        
        if chunk_count <= 5:  # Log first 5 chunks for debugging
            logger.info(f"Chunk {chunk_count}: {len(chunk)} chars, starts with: '{chunk[:50]}...'")
        
        start += size - overlap
    
    logger.info(f"[OK] Text chunking completed: {len(chunks)} chunks created")
    logger.info(f"Average chunk size: {sum(len(c) for c in chunks) / len(chunks):.1f} characters")
    
    return chunks
