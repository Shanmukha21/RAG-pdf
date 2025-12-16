from app.vectorstore import search
import os
import requests
import logging

# Configure logging
logger = logging.getLogger(__name__)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

def _ollama_generate(prompt: str) -> str:
    logger.info(f"Generating response using Ollama model: {OLLAMA_MODEL}")
    logger.info(f"Ollama host: {OLLAMA_HOST}")
    logger.info(f"Prompt length: {len(prompt)} characters")
    
    url = f"{OLLAMA_HOST}/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    
    logger.info("Sending request to Ollama API...")
    try:
        r = requests.post(url, json=payload, timeout=300)
        logger.info(f"Ollama API response status: {r.status_code}")
        r.raise_for_status()
        logger.info("[OK] Ollama API request successful")
    except requests.exceptions.HTTPError as e:
        logger.error(f"[ERROR] Ollama API HTTP error: {e}")
        try:
            body = r.text
            logger.error(f"Response body: {body}")
        except Exception:
            body = "<no response body>"
        if getattr(r, 'status_code', None) == 404:
            error_msg = (
                f"Ollama API returned 404 at {url}.\n"
                "Ensure the Ollama daemon is running and `OLLAMA_HOST` is correct.\n"
                "Start Ollama locally (example): `ollama serve` and retry.\n"
                f"Response body: {body}"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        error_msg = f"Ollama API HTTP error: {e}, response: {body}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to connect to Ollama at {OLLAMA_HOST}: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    logger.info("Parsing Ollama response...")
    try:
        data = r.json()
        response_text = data.get("response", "")
        logger.info(f"[OK] Generated response length: {len(response_text)} characters")
        return response_text
    except Exception as e:
        logger.error(f"[ERROR] Failed to parse Ollama response: {e}")
        raise RuntimeError(f"Invalid JSON response from Ollama: {e}") from e

def answer_question(question: str, session_id: str = None):
    from app.progress import progress_tracker
    
    logger.info(f"Processing question: '{question}'")
    
    logger.info("Step 1: Searching for relevant documents...")
    if session_id:
        progress_tracker.add_step(session_id, "[SEARCH] Searching documents...", "info")
    
    try:
        docs = search(question, k=5)
        logger.info(f"[OK] Found {len(docs)} relevant documents")
        if session_id:
            progress_tracker.add_step(session_id, f"[OK] Found {len(docs)} relevant documents", "success")
    except Exception as e:
        logger.error(f"[ERROR] Document search failed: {e}")
        if session_id:
            progress_tracker.add_step(session_id, "[ERROR] Document search failed", "error", str(e))
        raise RuntimeError(f"Failed to search documents: {e}") from e
    
    if not docs:
        logger.warning("No relevant documents found for the question")
        if session_id:
            progress_tracker.add_step(session_id, "[WARNING] No relevant documents found", "warning")
        return {
            "answer": "I don't have any relevant documents to answer this question. Please upload some documents first.",
            "sources": []
        }
    
    logger.info("Step 2: Building context from retrieved documents...")
    if session_id:
        progress_tracker.add_step(session_id, "[PROCESS] Building context from documents...", "info")
    
    context_parts = []
    for i, d in enumerate(docs, start=1):
        context_part = f"[{i}] Source: {d['source']}\n{d['text']}"
        context_parts.append(context_part)
        logger.info(f"Added context {i}: Source='{d['source']}', Length={len(d['text'])} chars")
    
    context = "\n\n".join(context_parts)
    logger.info(f"[OK] Built context with {len(context)} total characters")
    if session_id:
        progress_tracker.add_step(session_id, f"[OK] Built context: {len(context)} characters", "success")
    
    logger.info("Step 3: Constructing prompt for AI generation...")
    if session_id:
        progress_tracker.add_step(session_id, "[AI] Preparing AI prompt...", "info")
    
    prompt = f"""
You are a helpful assistant.
Answer the question using ONLY the context below.
When you use a fact, cite it like [1], [2], etc.
If the answer is not in the context, say: "I don't know based on the provided documents."

Context:
{context}

Question:
{question}

Answer:
"""
    logger.info(f"[OK] Constructed prompt with {len(prompt)} characters")
    
    logger.info("Step 4: Generating AI response...")
    if session_id:
        progress_tracker.add_step(session_id, "[AI] Generating AI response...", "info")
    
    try:
        answer = _ollama_generate(prompt)
        logger.info(f"[OK] Generated answer with {len(answer)} characters")
        if session_id:
            progress_tracker.add_step(session_id, f"[OK] AI response generated: {len(answer)} chars", "success")
    except Exception as e:
        logger.error(f"[ERROR] AI generation failed: {e}")
        if session_id:
            progress_tracker.add_step(session_id, "[ERROR] AI generation failed", "error", str(e))
        raise RuntimeError(f"Failed to generate answer: {e}") from e
    
    logger.info("Step 5: Preparing response with sources...")
    sources = [{"id": i+1, "source": d["source"]} for i, d in enumerate(docs)]
    logger.info(f"[OK] Prepared {len(sources)} source references")
    
    response = {
        "answer": answer.strip(),
        "sources": sources
    }
    
    logger.info("Question processing completed successfully")
    return response
