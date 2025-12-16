import streamlit as st
import os
import time
from src.document_processor import process_document
from src.vector_store import VectorStore
from src.rag_engine import RAGEngine
from src.utils import setup_logging

# Configure page
st.set_page_config(
    page_title="RAG System - Document Chat",
    page_icon="🤖",
    layout="wide"
)

# Setup logging
setup_logging()

# Custom CSS
st.markdown("""
<style>
.chat-message {
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    display: flex;
    flex-direction: column;
}
.user-message {
    background-color: #e3f2fd;
    border-left: 4px solid #2196f3;
}
.bot-message {
    background-color: #f1f8e9;
    border-left: 4px solid #4caf50;
}
.upload-section {
    background-color: #fff3e0;
    padding: 1rem;
    border-radius: 0.5rem;
    border: 2px dashed #ff9800;
    text-align: center;
    margin-bottom: 2rem;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "documents_uploaded" not in st.session_state:
    st.session_state.documents_uploaded = []
if "vector_store" not in st.session_state:
    st.session_state.vector_store = VectorStore()
if "rag_engine" not in st.session_state:
    st.session_state.rag_engine = RAGEngine()

# Header
st.title("🤖 RAG System - Document Chat")
st.markdown("*Upload documents and chat with them using AI-powered retrieval*")

# Sidebar for document upload
with st.sidebar:
    st.header("📄 Document Upload")
    
    uploaded_file = st.file_uploader(
        "Choose a document",
        type=["pdf", "txt"],
        help="Supports PDF and text files"
    )
    
    if uploaded_file:
        if uploaded_file.name not in st.session_state.documents_uploaded:
            with st.spinner("Processing document..."):
                try:
                    # Process document
                    chunks = process_document(uploaded_file.getvalue(), uploaded_file.name)
                    
                    # Add to vector store
                    st.session_state.vector_store.add_documents(chunks, uploaded_file.name)
                    
                    # Update state
                    st.session_state.documents_uploaded.append(uploaded_file.name)
                    
                    st.success(f"✅ {uploaded_file.name} processed successfully!")
                    
                    # Add system message
                    st.session_state.messages.append({
                        "role": "system",
                        "content": f"📄 Document '{uploaded_file.name}' has been uploaded and processed. You can now ask questions about it!"
                    })
                    
                except Exception as e:
                    st.error(f"❌ Processing failed: {e}")
        else:
            st.info(f"📄 {uploaded_file.name} already uploaded")
    
    # Show uploaded documents
    if st.session_state.documents_uploaded:
        st.subheader("📚 Uploaded Documents")
        for doc in st.session_state.documents_uploaded:
            st.write(f"• {doc}")
    
    # Vector store stats
    if hasattr(st.session_state.vector_store, 'get_stats'):
        stats = st.session_state.vector_store.get_stats()
        if stats['total_documents'] > 0:
            st.subheader("📊 Database Stats")
            st.write(f"Documents: {stats['total_documents']}")
            st.write(f"Chunks: {stats['total_chunks']}")
    
    # Clear chat button
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Main chat interface
if not st.session_state.documents_uploaded:
    st.markdown("""
    <div class="upload-section">
        <h3>👋 Welcome to RAG System!</h3>
        <p>Please upload a document from the sidebar to start chatting.</p>
        <p>📋 <strong>Features:</strong></p>
        <ul style="text-align: left; display: inline-block;">
            <li>Document ingestion (PDF, TXT)</li>
            <li>Intelligent chunking</li>
            <li>Vector embeddings</li>
            <li>Semantic search</li>
            <li>AI-powered answers with citations</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
else:
    # Display chat messages
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>🧑 You:</strong><br>
                {message["content"]}
            </div>
            """, unsafe_allow_html=True)
        elif message["role"] == "assistant":
            st.markdown(f"""
            <div class="chat-message bot-message">
                <strong>🤖 Assistant:</strong><br>
                {message["content"]}
            </div>
            """, unsafe_allow_html=True)
            
            # Show sources if available
            if "sources" in message:
                with st.expander("📚 Sources"):
                    for i, source in enumerate(message["sources"], 1):
                        st.write(f"{i}. {source.get('source', 'Unknown')}")
        elif message["role"] == "system":
            st.info(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask a question about your documents..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message immediately
        st.markdown(f"""
        <div class="chat-message user-message">
            <strong>🧑 You:</strong><br>
            {prompt}
        </div>
        """, unsafe_allow_html=True)
        
        # Get AI response
        with st.spinner("🤖 Thinking..."):
            try:
                result = st.session_state.rag_engine.answer_question(
                    prompt, 
                    st.session_state.vector_store
                )
                
                answer = result.get("answer", "I couldn't generate an answer.")
                sources = result.get("sources", [])
                
                # Add assistant message
                assistant_message = {
                    "role": "assistant", 
                    "content": answer,
                    "sources": sources
                }
                st.session_state.messages.append(assistant_message)
                
                # Display assistant message
                st.markdown(f"""
                <div class="chat-message bot-message">
                    <strong>🤖 Assistant:</strong><br>
                    {answer}
                </div>
                """, unsafe_allow_html=True)
                
                # Show sources
                if sources:
                    with st.expander("📚 Sources"):
                        for i, source in enumerate(sources, 1):
                            st.write(f"{i}. {source.get('source', 'Unknown')}")
                
            except Exception as e:
                error_msg = f"❌ Sorry, I encountered an error: {e}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
        
        # Rerun to show the new messages
        st.rerun()