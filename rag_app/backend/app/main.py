from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from app.ingest import ingest_document
from app import vectorstore as _vectorstore
from app.rag import answer_question
from app.progress import progress_tracker
from pydantic import BaseModel
import logging
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('rag_backend.log')
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="RAG System")

class Query(BaseModel):
    question: str

@app.post("/ingest")
async def ingest(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    session_id = str(uuid.uuid4())
    progress_tracker.start_session(session_id)
    
    logger.info(f"[FILE] Received file upload: {file.filename}")
    progress_tracker.add_step(session_id, f"[FILE] Received file: {file.filename}", "info")
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        logger.warning(f"[ERROR] Invalid file type: {file.filename}")
        progress_tracker.add_step(session_id, "[ERROR] Invalid file type", "error", "Only PDF files are supported")
        return {"status": "error", "message": "Only PDF files are supported", "session_id": session_id}
    
    progress_tracker.add_step(session_id, "[OK] File type validated", "success")
    
    logger.info("[READ] Reading file bytes...")
    progress_tracker.add_step(session_id, "[read] Reading file bytes...", "info")
    
    try:
        file_bytes = await file.read()
        logger.info(f"✅ File read successfully: {len(file_bytes)} bytes")
        progress_tracker.add_step(session_id, f"[OK] File read: {len(file_bytes)} bytes", "success")
    except Exception as e:
        logger.error(f"❌ Failed to read file: {e}")
        progress_tracker.add_step(session_id, "[ERROR] File read failed", "error", str(e))
        return {"status": "error", "message": f"Failed to read file: {e}", "session_id": session_id}
    
    logger.info("[QUEUE] Adding ingestion task to background queue...")
    progress_tracker.add_step(session_id, "[QUEUE] Starting background processing...", "info")
    
    # Modified background task to include session_id
    background_tasks.add_task(ingest_document_with_progress, file_bytes, file.filename, session_id)
    logger.info("✅ Ingestion task queued successfully")
    
    return {"status": "ingestion started", "filename": file.filename, "session_id": session_id}


@app.on_event("startup")
def startup_event():
    logger.info("[START] Starting RAG Backend Server...")
    logger.info("[SETUP] Pre-warming vector store components...")
    try:
        _vectorstore._ensure_initialized()
        logger.info("[OK] Vector store pre-warming completed")
    except Exception as e:
        logger.warning(f"[WARNING] Vector store pre-warming failed: {e}")
        logger.info("[INFO] Components will be initialized on first use")
    logger.info("[COMPLETE] RAG Backend Server startup completed")

@app.post("/query")
def query(q: Query):
    session_id = str(uuid.uuid4())
    progress_tracker.start_session(session_id)
    
    logger.info(f"[QUERY] Received query: '{q.question}'")
    progress_tracker.add_step(session_id, f"[QUERY] Processing query: {q.question[:50]}...", "info")
    
    try:
        result = answer_question_with_progress(q.question, session_id)
        logger.info("✅ Query processed successfully")
        progress_tracker.add_step(session_id, "[OK] Query completed successfully", "success")
        progress_tracker.end_session(session_id)
        
        result["session_id"] = session_id
        return result
    except Exception as e:
        logger.error(f"❌ Query processing failed: {e}")
        progress_tracker.add_step(session_id, "[ERROR] Query failed", "error", str(e))
        progress_tracker.end_session(session_id)
        return {"status": "error", "message": str(e), "session_id": session_id}

@app.get("/health")
def health():
    logger.info("[HEALTH] Health check requested")
    return {"status": "ok", "message": "RAG Backend is running"}

@app.get("/progress/{session_id}")
def get_progress(session_id: str):
    """Get progress updates for a specific session"""
    progress = progress_tracker.get_progress(session_id)
    return {"session_id": session_id, "progress": progress}

# Wrapper functions with progress tracking
def ingest_document_with_progress(file_bytes: bytes, filename: str, session_id: str):
    """Wrapper for ingest_document with progress tracking"""
    try:
        progress_tracker.add_step(session_id, "[PROCESS] Starting document processing...", "info")
        ingest_document(file_bytes, filename, session_id)
        progress_tracker.add_step(session_id, "[OK] Document ingestion completed", "success")
        progress_tracker.end_session(session_id)
    except Exception as e:
        progress_tracker.add_step(session_id, "[ERROR] Document ingestion failed", "error", str(e))
        progress_tracker.end_session(session_id)
        logger.error(f"Background ingestion failed: {e}")

def answer_question_with_progress(question: str, session_id: str):
    """Wrapper for answer_question with progress tracking"""
    progress_tracker.add_step(session_id, "[SEARCH] Starting question processing...", "info")
    
    try:
        result = answer_question(question, session_id)
        return result
    except Exception as e:
        progress_tracker.add_step(session_id, "[ERROR] Question processing failed", "error", str(e))
        raise


if __name__ == "__main__":
    import uvicorn
    
    logger.info("[START] Starting RAG Backend Server...")
    # Pass the application as an import string so "reload" works correctly
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
