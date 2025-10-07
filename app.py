"""
Streamlit App for Document Chat Bot
Multi-document chat interface for PDF documents
"""

import streamlit as st
from goldmansachs.awm_genai import LLM, LLMConfig
import config
from datetime import datetime
import tempfile
import os
import pdfplumber

# Page configuration
st.set_page_config(
    page_title="Document Chat Bot",
    page_icon="📄",
    layout="wide"
)

# Initialize session state
if 'extracted_text' not in st.session_state:
    st.session_state.extracted_text = None
if 'llm' not in st.session_state:
    st.session_state.llm = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'uploaded_files_info' not in st.session_state:
    st.session_state.uploaded_files_info = []

# Custom CSS
st.markdown("""
<style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 3px solid #0066cc;
    }
    .user-message {
        background-color: #e3f2fd;
    }
    .assistant-message {
        background-color: #f5f5f5;
    }
    .doc-info {
        background-color: #fff3cd;
        padding: 0.5rem;
        border-radius: 0.3rem;
        margin: 0.3rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("Configuration")
    
    # Application Configuration
    st.subheader("Settings")
    app_id = st.text_input("App ID", value=config.APP_ID)
    env = st.selectbox("Environment", ["uat", "prod"], index=0 if config.ENV == "uat" else 1)
    
    st.markdown("---")
    
    # Model Configuration
    st.subheader("Model Settings")
    model_name = st.selectbox(
        "Select Model",
        config.AVAILABLE_MODELS,
        index=config.AVAILABLE_MODELS.index(config.DEFAULT_MODEL),
        help="Choose between Pro (more capable) or Flash Lite (faster)"
    )
    temperature = st.slider("Temperature", 0.0, 1.0, float(config.DEFAULT_TEMPERATURE), 0.1)
    log_level = st.selectbox("Log Level", ["DEBUG", "INFO", "WARNING", "ERROR"], index=0)
    
    st.markdown("---")
    
    # Document Upload
    st.subheader("Upload Documents")
    uploaded_files = st.file_uploader(
        "Choose PDF files",
        type=config.SUPPORTED_FILE_TYPES,
        accept_multiple_files=True,
        help=f"Upload up to {config.MAX_DOCUMENTS} PDF files (max {config.MAX_FILE_SIZE_MB}MB each)"
    )
    
    if st.button("Process Documents", type="primary", disabled=not uploaded_files):
        if len(uploaded_files) > config.MAX_DOCUMENTS:
            st.error(f"Maximum {config.MAX_DOCUMENTS} documents allowed")
        else:
            with st.spinner("Extracting text from PDFs..."):
                try:
                    all_text = []
                    
                    # Extract text from each PDF
                    for uploaded_file in uploaded_files:
                        # Save to temp file
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            tmp_path = tmp_file.name
                        
                        try:
                            # Extract text using pdfplumber
                            with pdfplumber.open(tmp_path) as pdf:
                                doc_text = f"\n\n--- Document: {uploaded_file.name} ---\n\n"
                                for page_num, page in enumerate(pdf.pages, 1):
                                    text = page.extract_text()
                                    if text:
                                        doc_text += f"\n[Page {page_num}]\n{text}\n"
                                all_text.append(doc_text)
                        finally:
                            # Clean up temp file
                            os.unlink(tmp_path)
                    
                    # Combine all extracted text
                    st.session_state.extracted_text = "\n\n".join(all_text)
                    
                    # Initialize LLM
                    llm_config = LLMConfig(
                        app_id=app_id,
                        env=env,
                        model_name=model_name,
                        temperature=temperature,
                        log_level=log_level,
                    )
                    st.session_state.llm = LLM.init(config=llm_config)
                    
                    # Store file info
                    st.session_state.uploaded_files_info = [
                        {"name": f.name, "size": f.size} for f in uploaded_files
                    ]
                    
                    st.success(f"Successfully processed {len(uploaded_files)} documents!")
                    st.session_state.chat_history = []  # Reset chat history
                    st.rerun()  # Refresh to show chat interface
                    
                except Exception as e:
                    st.error(f"Error processing documents: {str(e)}")
    
    # Display uploaded documents
    if st.session_state.uploaded_files_info:
        st.markdown("---")
        st.subheader("Loaded Documents")
        for i, doc_info in enumerate(st.session_state.uploaded_files_info, 1):
            st.markdown(f"""
            <div class="doc-info">
                {i}. {doc_info['name']}<br>
                <small>Size: {doc_info['size'] / 1024:.2f} KB</small>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Clear chat button
    if st.session_state.chat_history and st.button("Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()

# Main content
st.title("Document Chat Bot")
st.markdown("Ask questions about your uploaded documents.")

# Instructions
if not st.session_state.extracted_text:
    st.info("""
    **Getting Started:**
    1. Configure your App ID and Environment in the sidebar
    2. Upload one or more PDF documents
    3. Click 'Process Documents' to extract text
    4. Start asking questions about your documents
    """)
else:
    # Show ready message
    st.success(f"Ready to chat! {len(st.session_state.uploaded_files_info)} documents loaded.")
    
    # Display chat history
    for message in st.session_state.chat_history:
        # User message
        st.markdown(f"""
        <div class="chat-message user-message">
            <strong>You:</strong><br>
            {message['question']}
        </div>
        """, unsafe_allow_html=True)
        
        # Assistant message
        st.markdown(f"""
        <div class="chat-message assistant-message">
            <strong>Assistant:</strong><br>
            {message['response']}
        </div>
        """, unsafe_allow_html=True)
    
    # Chat input - always visible when documents are loaded
    prompt = st.chat_input("Ask a question about your documents...")
    
    if prompt:
        # Display user message immediately
        st.session_state.chat_history.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "question": prompt,
            "response": "..."
        })
        
        with st.spinner("Generating response..."):
            try:
                # Create prompt with document context
                full_prompt = f"""Based on the following document content, please answer the question.

Document Content:
{st.session_state.extracted_text}

Question: {prompt}

Please provide a detailed answer based only on the information in the documents above. If the information is not in the documents, please say so."""
                
                # Get response from LLM
                response = st.session_state.llm.invoke(full_prompt)
                
                # Update chat history with actual response
                st.session_state.chat_history[-1]["response"] = response
                
                # Rerun to display new message
                st.rerun()
                
            except Exception as e:
                st.session_state.chat_history[-1]["response"] = f"Error: {str(e)}"
                st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <small>Multi-Document Chat System</small>
</div>
""", unsafe_allow_html=True)

