import os
import streamlit as st
import requests
import time

API = os.getenv("API_URL", "http://127.0.0.1:8000")

# Page config
st.set_page_config(
    page_title="PDF Chat Assistant",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS for chat-like appearance
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
if "pdf_uploaded" not in st.session_state:
    st.session_state.pdf_uploaded = False
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

# Header
st.title("🤖 PDF Chat Assistant")
st.markdown("*Upload your PDF documents and chat with them using AI*")

# Sidebar for PDF upload
with st.sidebar:
    st.header("📄 Document Upload")
    
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        help="Only PDF files are supported"
    )
    
    if uploaded_file:
        if uploaded_file.name not in st.session_state.uploaded_files:
            with st.spinner("Processing PDF..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                try:
                    resp = requests.post(f"{API}/ingest", files=files, timeout=300)
                    resp.raise_for_status()
                    st.session_state.uploaded_files.append(uploaded_file.name)
                    st.session_state.pdf_uploaded = True
                    st.success(f"✅ {uploaded_file.name} uploaded successfully!")
                    
                    # Add system message
                    st.session_state.messages.append({
                        "role": "system",
                        "content": f"📄 Document '{uploaded_file.name}' has been uploaded and processed. You can now ask questions about it!"
                    })
                    
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Upload failed: {e}")
        else:
            st.info(f"📄 {uploaded_file.name} already uploaded")
    
    # Show uploaded files
    if st.session_state.uploaded_files:
        st.subheader("📚 Uploaded Documents")
        for file in st.session_state.uploaded_files:
            st.write(f"• {file}")
    
    # Clear chat button
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Main chat interface
if not st.session_state.pdf_uploaded:
    st.markdown("""
    <div class="upload-section">
        <h3>👋 Welcome to PDF Chat Assistant!</h3>
        <p>Please upload a PDF document from the sidebar to start chatting.</p>
        <p>📋 <strong>What you can do:</strong></p>
        <ul style="text-align: left; display: inline-block;">
            <li>Upload PDF documents</li>
            <li>Ask questions about the content</li>
            <li>Get AI-powered answers with citations</li>
            <li>Chat naturally about your documents</li>
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
    if prompt := st.chat_input("Ask a question about your PDF..."):
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
                resp = requests.post(f"{API}/query", json={"question": prompt}, timeout=300)
                resp.raise_for_status()
                data = resp.json()
                
                answer = data.get("answer", "I couldn't generate an answer.")
                sources = data.get("sources", [])
                
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
                
            except requests.exceptions.RequestException as e:
                error_msg = f"❌ Sorry, I encountered an error: {e}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
            except ValueError:
                error_msg = "❌ Received invalid response from server. Please check if the backend is running."
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
        
        # Rerun to show the new messages
        st.rerun()
