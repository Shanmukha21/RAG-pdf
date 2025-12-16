# RAG Application - Standalone Version

This is a simplified version of the RAG application that runs without Docker.

## Prerequisites

1. **Python 3.8+** installed
2. **Ollama** installed and running
   - Download from: https://ollama.ai
   - Start with: `ollama serve`
   - Pull model: `ollama pull llama3.2:3b`

## Quick Start

### Option 1: Automated Setup
```bash
python setup_and_run.py
```

### Option 2: Manual Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Start backend server:**
```bash
python run_backend.py
```

3. **Start frontend (in another terminal):**
```bash
python run_frontend.py
```

## Usage

1. Open http://localhost:8501 in your browser
2. Upload a document (PDF or text file)
3. Ask questions about the document
4. Get AI-generated answers with source citations

## API Endpoints

- **Backend**: http://127.0.0.1:8000
  - `POST /ingest` - Upload documents
  - `POST /query` - Ask questions
  - `GET /health` - Health check

- **Frontend**: http://localhost:8501

## Troubleshooting

### Common Issues:

1. **"Failed to connect to Ollama"**
   - Make sure Ollama is running: `ollama serve`
   - Check if model is available: `ollama list`
   - Pull model if missing: `ollama pull llama3.2:3b`

2. **"Vector store not initialized"**
   - Check if sentence-transformers is installed
   - Ensure internet connection for model download

3. **"Module not found"**
   - Run: `pip install -r requirements.txt`

4. **Empty search results**
   - Upload documents first before asking questions
   - Check if documents were processed successfully

### File Structure:
```
rag_app_sowmya/
├── requirements.txt          # All dependencies
├── setup_and_run.py         # Automated setup
├── run_backend.py           # Backend runner
├── run_frontend.py          # Frontend runner
├── rag_app/
│   ├── backend/
│   │   └── app/             # FastAPI backend
│   └── frontend/
│       └── app.py           # Streamlit frontend
├── faiss.index             # Vector database (created after first upload)
└── meta.pkl                # Document metadata (created after first upload)
```

## What This Application Does

1. **Document Upload**: Processes PDF/text files into searchable chunks
2. **Vector Storage**: Creates embeddings using sentence-transformers
3. **Semantic Search**: Finds relevant document sections using FAISS
4. **AI Generation**: Uses Ollama to generate contextual answers
5. **Source Attribution**: Provides citations for fact-checking