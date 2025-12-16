#!/usr/bin/env python3
"""
Run the RAG backend server
Usage: python run_backend.py
"""
import sys
import os

# Add the backend app to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rag_app', 'backend'))

if __name__ == "__main__":
    import uvicorn
    
    print("Starting RAG Backend Server...")
    print("Server will be available at: http://127.0.0.1:8000")
    print("API endpoints:")
    print("  - POST /ingest - Upload documents")
    print("  - POST /query - Ask questions")
    print("  - GET /health - Health check")
    print("\nPress Ctrl+C to stop the server")
    
    # Change to backend directory for proper file paths
    os.chdir(os.path.join(os.path.dirname(__file__), 'rag_app', 'backend'))
    
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)