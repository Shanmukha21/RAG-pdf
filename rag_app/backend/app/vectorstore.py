import faiss
import os
from sentence_transformers import SentenceTransformer
import numpy as np
import pickle
import threading
import logging

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

DIM = 384
INDEX_PATH = "faiss.index"
META_PATH = "meta.pkl"

# Lazily initialized globals
_model = None
_index = None
_metadata = None
_init_lock = threading.Lock()

def _ensure_initialized():
    global _model, _index, _metadata
    if _model is not None and _index is not None and _metadata is not None:
        logger.info("Vector store already initialized")
        return
    
    logger.info("Initializing vector store components...")
    with _init_lock:
        if _model is None:
            try:
                logger.info("Loading SentenceTransformer model: all-MiniLM-L6-v2")
                _model = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("[OK] SentenceTransformer model loaded successfully")
            except Exception as e:
                logger.error(f"[ERROR] Failed to load SentenceTransformer model: {e}")
                _model = None
        
        if _index is None:
            try:
                if os.path.exists(INDEX_PATH):
                    logger.info(f"Loading existing FAISS index from {INDEX_PATH}")
                    _index = faiss.read_index(INDEX_PATH)
                    logger.info(f"[OK] FAISS index loaded with {_index.ntotal} vectors")
                else:
                    logger.info(f"Creating new FAISS index with dimension {DIM}")
                    _index = faiss.IndexFlatL2(DIM)
                    logger.info("[OK] New FAISS index created")
            except Exception as e:
                logger.error(f"[ERROR] Failed to load FAISS index: {e}")
                logger.info(f"Creating fallback FAISS index with dimension {DIM}")
                _index = faiss.IndexFlatL2(DIM)
        
        if _metadata is None:
            try:
                if os.path.exists(META_PATH):
                    logger.info(f"Loading metadata from {META_PATH}")
                    with open(META_PATH, "rb") as f:
                        _metadata = pickle.load(f)
                    logger.info(f"[OK] Metadata loaded with {len(_metadata)} entries")
                else:
                    logger.info("Creating new metadata store")
                    _metadata = []
                    logger.info("[OK] New metadata store created")
            except Exception as e:
                logger.error(f"[ERROR] Failed to load metadata: {e}")
                logger.info("Creating fallback metadata store")
                _metadata = []
    
    logger.info("Vector store initialization completed")

def add_documents(chunks, source):
    logger.info(f"Starting document ingestion for source: {source}")
    logger.info(f"Number of chunks to process: {len(chunks)}")
    
    _ensure_initialized()
    global _metadata, _index, _model
    
    if _model is None or _index is None:
        error_msg = "Vector store not initialized properly"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    logger.info("Generating embeddings for document chunks...")
    try:
        embeddings = _model.encode(chunks)
        logger.info(f"[OK] Generated {len(embeddings)} embeddings")
    except Exception as e:
        logger.error(f"[ERROR] Failed to generate embeddings: {e}")
        raise
    
    logger.info("Adding embeddings to FAISS index...")
    try:
        _index.add(np.array(embeddings).astype("float32"))
        logger.info(f"[OK] Added {len(embeddings)} vectors to index (total: {_index.ntotal})")
    except Exception as e:
        logger.error(f"[ERROR] Failed to add vectors to index: {e}")
        raise
    
    logger.info("Updating metadata store...")
    _metadata.extend([{"text": c, "source": source} for c in chunks])
    logger.info(f"[OK] Added {len(chunks)} metadata entries (total: {len(_metadata)})")
    
    logger.info("Persisting index and metadata to disk...")
    try:
        faiss.write_index(_index, INDEX_PATH)
        logger.info(f"[OK] FAISS index saved to {INDEX_PATH}")
        
        with open(META_PATH, "wb") as f:
            pickle.dump(_metadata, f)
        logger.info(f"[OK] Metadata saved to {META_PATH}")
        
    except Exception as e:
        logger.error(f"[ERROR] Failed to persist data: {e}")
        logger.warning("Data added to memory but not saved to disk")
    
    logger.info(f"Document ingestion completed for {source}")

def search(query, k=5):
    logger.info(f"Starting search for query: '{query[:100]}...' (k={k})")
    
    _ensure_initialized()
    global _model, _index, _metadata
    
    if _model is None or _index is None:
        logger.warning("Vector store not properly initialized for search")
        return []
    
    if not _metadata:
        logger.warning("No documents in metadata store - empty search results")
        return []
    
    logger.info(f"Vector store status: {_index.ntotal} vectors, {len(_metadata)} metadata entries")
    
    logger.info("Generating query embedding...")
    try:
        emb = _model.encode([query])
        logger.info("[OK] Query embedding generated")
    except Exception as e:
        logger.error(f"[ERROR] Failed to generate query embedding: {e}")
        return []
    
    logger.info("Performing similarity search...")
    try:
        D, I = _index.search(np.array(emb).astype("float32"), k)
        logger.info(f"[OK] Search completed, found {len(I[0])} results")
        logger.info(f"Distances: {D[0].tolist()}")
        logger.info(f"Indices: {I[0].tolist()}")
    except Exception as e:
        logger.error(f"[ERROR] Search failed: {e}")
        return []
    
    logger.info("Retrieving metadata for results...")
    results = []
    for i, idx in enumerate(I[0]):
        if idx < len(_metadata):
            result = _metadata[idx]
            results.append(result)
            logger.info(f"Result {i+1}: Source='{result['source']}', Text='{result['text'][:100]}...'")
        else:
            logger.warning(f"Index {idx} out of range for metadata (size: {len(_metadata)})")
    
    logger.info(f"Search completed, returning {len(results)} results")
    return results