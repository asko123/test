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
from pdf_extractor import PDFExtractor
from json_extractor import JSONExtractor

# Page configuration
st.set_page_config(
    page_title="Document Chat Bot",
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
        padding: 1.2rem;
        border-radius: 0.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #1976d2;
    }
    .assistant-message {
        background-color: #ffffff;
        border-left: 4px solid #4caf50;
        line-height: 1.6;
        font-size: 0.95rem;
    }
    .assistant-message p {
        margin: 0.5rem 0;
    }
    .assistant-message ul, .assistant-message ol {
        margin: 0.5rem 0;
        padding-left: 1.5rem;
    }
    .doc-info {
        background-color: #fff3cd;
        padding: 0.5rem;
        border-radius: 0.3rem;
        margin: 0.3rem 0;
    }
    
    /* Improve selectbox visibility */
    .stSelectbox {
        background-color: white;
    }
    .stSelectbox > div > div {
        background-color: white;
        border: 2px solid #1f77b4;
    }
    .stSelectbox label {
        color: #262730;
        font-weight: 600;
        font-size: 1rem;
    }
    
    /* Improve text input visibility */
    .stTextInput > div > div > input {
        background-color: white;
        border: 2px solid #1f77b4;
        color: #262730;
    }
    
    /* Improve slider visibility */
    .stSlider > div > div > div {
        background-color: #1f77b4;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #f0f2f6;
    }
    
    /* Make dropdown options more visible */
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: white;
        color: #262730;
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
        "Choose files",
        type=config.SUPPORTED_FILE_TYPES,
        accept_multiple_files=True,
        help=f"Upload up to {config.MAX_DOCUMENTS} files (PDF, JSON, JSONL, or TXT) - max {config.MAX_FILE_SIZE_MB}MB each"
    )
    
    if st.button("Process Documents", type="primary", disabled=not uploaded_files):
        if len(uploaded_files) > config.MAX_DOCUMENTS:
            st.error(f"Maximum {config.MAX_DOCUMENTS} documents allowed")
        else:
            with st.spinner("Processing documents..."):
                try:
                    # Initialize extractors
                    pdf_extractor = PDFExtractor()
                    json_extractor = JSONExtractor()
                    
                    all_content = []
                    
                    # Process each uploaded file based on type
                    for uploaded_file in uploaded_files:
                        file_ext = uploaded_file.name.split('.')[-1].lower()
                        
                        # Save to temp file
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}') as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            tmp_path = tmp_file.name
                        
                        try:
                            if file_ext == 'pdf':
                                # Extract from PDF
                                content = pdf_extractor.extract_from_file(tmp_path, uploaded_file.name)
                                all_content.append(content)
                            elif file_ext == 'json':
                                # Extract from JSON
                                content = json_extractor.extract_from_json_file(tmp_path, uploaded_file.name)
                                all_content.append(content)
                            elif file_ext == 'jsonl':
                                # Extract from JSONL
                                content = json_extractor.extract_from_jsonl_file(tmp_path, uploaded_file.name)
                                all_content.append(content)
                            elif file_ext == 'txt':
                                # Extract from text file
                                with open(tmp_path, 'r', encoding='utf-8') as f:
                                    text_content = f.read()
                                formatted_txt = f"\n\n{'='*80}\nDocument: {uploaded_file.name}\n{'='*80}\n\n{text_content}\n"
                                all_content.append(formatted_txt)
                        finally:
                            os.unlink(tmp_path)
                    
                    # Combine all extracted content
                    st.session_state.extracted_text = "\n\n".join(all_content)
                    
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
            <strong>Question:</strong><br>
            {message['question']}
        </div>
        """, unsafe_allow_html=True)
        
        # Response message - formatted
        formatted_response = message['response'].strip()
        st.markdown(f"""
        <div class="chat-message assistant-message">
            {formatted_response}
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
                full_prompt = f"""You are a cybersecurity and risk analysis assistant. Your role is to help users understand security controls, compliance requirements, risk assessments, and related governance documentation.

The documents may contain:
- Security controls and compliance frameworks
- Risk assessment data and audit findings
- Policy documents and governance standards
- Tables with control mappings, risk metrics, or compliance data
- Structured JSON/JSONL with control definitions, asset types, or security configurations
- Regular text describing security procedures and requirements

Document Content:
{st.session_state.extracted_text}

Question: {prompt}

Instructions:
1. Provide accurate, detailed answers based ONLY on the information in the provided documents
2. For security controls: Always include control IDs, names, and descriptions when available
3. For risk-related queries: Highlight severity, impact, likelihood, and mitigation measures
4. For compliance questions: Reference specific requirements, standards, and responsible parties
5. Format your response professionally:
   - Use bullet points for lists of controls, risks, or requirements
   - Use numbered lists for sequential procedures or steps
   - Bold or highlight critical security information
   - Include clear paragraph breaks for readability
6. Always cite your sources precisely:
   - For tables: "according to Table 2 on Page 5"
   - For JSON data: "from JSON Object 3 (control_id: 3997)"
   - For specific fields: mention field names (e.g., "responsible_party", "asset_type")
7. If information is missing or unclear, explicitly state what is available and what is not
8. Do not include raw JSON dumps or unformatted data - present information in a readable format
9. For questions about multiple controls or risks, organize your response systematically

Answer:"""
                
                # Get response from LLM
                response = st.session_state.llm.invoke(full_prompt)
                
                # Extract actual content from response
                actual_response = None
                
                # Try different response formats
                try:
                    # Method 1: Check for content attribute
                    if hasattr(response, 'content'):
                        actual_response = response.content
                    # Method 2: Check if it's a dict with Response.content
                    elif isinstance(response, dict):
                        if 'Response' in response and isinstance(response['Response'], dict):
                            actual_response = response['Response'].get('content', None)
                        elif 'content' in response:
                            actual_response = response['content']
                        else:
                            # Try to find any key that might contain the answer
                            for key in ['answer', 'text', 'message', 'result']:
                                if key in response:
                                    actual_response = response[key]
                                    break
                    # Method 3: It's already a string
                    elif isinstance(response, str):
                        actual_response = response
                    
                    # If still None, convert to string
                    if actual_response is None:
                        actual_response = str(response)
                    
                    # Clean up escape sequences
                    if isinstance(actual_response, str):
                        actual_response = actual_response.replace('\\n\\n', '\n\n')
                        actual_response = actual_response.replace('\\n', '\n')
                        actual_response = actual_response.replace('\\t', '\t')
                        actual_response = actual_response.strip()
                    
                except Exception as parse_error:
                    actual_response = f"[ERROR] Failed to parse response: {str(parse_error)}\n\nRaw response: {str(response)[:500]}"
                
                # Final check
                if not actual_response or actual_response.strip() == "":
                    actual_response = f"[ERROR] Empty response received. Response type: {type(response).__name__}"
                
                # Update chat history with actual response
                st.session_state.chat_history[-1]["response"] = actual_response
                
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

