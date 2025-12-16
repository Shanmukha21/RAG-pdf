#!/usr/bin/env python3
"""
Run the RAG frontend (Streamlit app)
Usage: python run_frontend.py
"""
import sys
import os
import subprocess

if __name__ == "__main__":
    print("Starting RAG Frontend (Streamlit)...")
    print("Make sure the backend is running at http://127.0.0.1:8000")
    print("Frontend will be available at: http://localhost:8501")
    print("\nPress Ctrl+C to stop the frontend")
    
    # Change to frontend directory
    frontend_dir = os.path.join(os.path.dirname(__file__), 'rag_app', 'frontend')
    os.chdir(frontend_dir)
    
    # Run streamlit
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])