"""
Streamlit App for Document Chat Bot
Multi-document chat interface for PDF documents
Enhanced with LangGraph ReAct Agent capabilities
"""

import sys
import os
from pathlib import Path

# Ensure current directory is in Python path for imports
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

import streamlit as st
from goldmansachs.awm_genai import LLM, LLMConfig
import config
from datetime import datetime
import tempfile
import json
from pdf_extractor import PDFExtractor
from json_extractor import JSONExtractor
from kg_retriever import KGRetriever

# Import agent modules with error handling
try:
    from query_router import QueryRouter
    from react_agent import AgentOrchestrator
    from agent_state import AgentState
    AGENT_MODULES_AVAILABLE = True
except ImportError as e:
    AGENT_MODULES_AVAILABLE = False
    AGENT_IMPORT_ERROR = str(e)
    print(f"[WARNING] Agent modules not available: {e}")
    print(f"[INFO] Current directory: {current_dir}")
    print(f"[INFO] Python path: {sys.path[:3]}")
    # Create dummy classes to prevent errors
    QueryRouter = None
    AgentOrchestrator = None
    AgentState = None

# Import Vespa with error handling
try:
    from vespa_search import VespaSearchWrapper, create_vespa_wrapper
    VESPA_AVAILABLE = True
except ImportError as e:
    VESPA_AVAILABLE = False
    VESPA_IMPORT_ERROR = str(e)
    VespaSearchWrapper = None
    create_vespa_wrapper = None

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
if 'kg_retriever' not in st.session_state:
    st.session_state.kg_retriever = None
if 'use_kg' not in st.session_state:
    st.session_state.use_kg = True

# Agent-related session state
if 'enable_agent' not in st.session_state:
    st.session_state.enable_agent = config.AGENT_DEFAULT_ENABLED
if 'agent_orchestrator' not in st.session_state:
    st.session_state.agent_orchestrator = None
if 'query_router' not in st.session_state:
    st.session_state.query_router = None
if 'agent_state' not in st.session_state:
    st.session_state.agent_state = None
if 'show_agent_trace' not in st.session_state:
    st.session_state.show_agent_trace = config.SHOW_AGENT_REASONING

# Vespa-related session state
if 'vespa_wrapper' not in st.session_state:
    st.session_state.vespa_wrapper = None
if 'enable_vespa' not in st.session_state:
    st.session_state.enable_vespa = config.ENABLE_VESPA_SEARCH
if 'vespa_schema_id' not in st.session_state:
    st.session_state.vespa_schema_id = config.VESPA_SCHEMA_ID
if 'vespa_env' not in st.session_state:
    st.session_state.vespa_env = config.VESPA_ENV

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
    
    # Knowledge Graph Settings
    st.subheader("Knowledge Graph")
    use_kg = st.checkbox(
        "Enable Knowledge Graph Enhancement",
        value=st.session_state.use_kg,
        help="Use Knowledge Graph to improve response quality by tracking entities and relationships"
    )
    st.session_state.use_kg = use_kg
    
    if use_kg and st.session_state.kg_retriever:
        with st.expander("View KG Statistics"):
            st.markdown(st.session_state.kg_retriever.export_graph_summary())
    
    st.markdown("---")
    
    # Vespa Vector Store Settings
    if config.ENABLE_VESPA_SEARCH and VESPA_AVAILABLE:
        st.subheader("Vespa Vector Store")
        enable_vespa = st.checkbox(
            "Enable Vespa Search",
            value=st.session_state.enable_vespa,
            help="Use Vespa vector database for additional context. Automatically used as fallback when no documents uploaded."
        )
        st.session_state.enable_vespa = enable_vespa
        
        if enable_vespa:
            vespa_schema_id = st.text_input(
                "Vespa Schema ID",
                value=st.session_state.vespa_schema_id,
                help="Schema identifier in Vespa DB"
            )
            st.session_state.vespa_schema_id = vespa_schema_id
            
            vespa_env = st.selectbox(
                "Vespa Environment",
                ["dev", "uat", "prod"],
                index=["dev", "uat", "prod"].index(st.session_state.vespa_env),
                help="Vespa environment to connect to"
            )
            st.session_state.vespa_env = vespa_env
            
            # Authentication fields
            st.markdown("**Authentication (Optional)**")
            vespa_gssso = st.text_input(
                "GSSO Token",
                type="password",
                help="Optional GSSO token for authentication. Required if getting 401/500 errors."
            )
            
            vespa_api_key = st.text_input(
                "API Key",
                type="password",
                help="Optional API key for authentication"
            )
            
            # Initialize Vespa wrapper
            if st.button("Connect to Vespa", type="secondary"):
                with st.spinner("Connecting to Vespa..."):
                    try:
                        vespa_wrapper = create_vespa_wrapper(
                            schema_id=vespa_schema_id,
                            env=vespa_env,
                            gssso=vespa_gssso if vespa_gssso else None,
                            x_api_key=vespa_api_key if vespa_api_key else None
                        )
                        if vespa_wrapper and vespa_wrapper.is_available():
                            # Test connection
                            test_result = vespa_wrapper.test_connection()
                            
                            if test_result.get('success'):
                                st.session_state.vespa_wrapper = vespa_wrapper
                                st.success(f"Connected to Vespa: {vespa_schema_id} ({vespa_env})")
                                
                                # Initialize agent with Vespa if enabled and not already initialized
                                if (config.ENABLE_AGENT_MODE and 
                                    st.session_state.enable_agent and 
                                    AGENT_MODULES_AVAILABLE and 
                                    not st.session_state.agent_orchestrator):
                                
                                with st.spinner("Initializing agent with Vespa..."):
                                    try:
                                        # Create minimal KG for agent
                                        if not st.session_state.kg_retriever:
                                            kg_retriever = KGRetriever()
                                            st.session_state.kg_retriever = kg_retriever
                                        
                                        # Create query router
                                        st.session_state.query_router = QueryRouter(
                                            complexity_threshold=config.AGENT_COMPLEXITY_THRESHOLD
                                        )
                                        
                                        # Initialize LLM if not already done
                                        if not st.session_state.llm:
                                            llm_config = LLMConfig(
                                                app_id=app_id,
                                                env=env,
                                                model_name=model_name,
                                                temperature=temperature,
                                                log_level=log_level,
                                            )
                                            st.session_state.llm = LLM.init(config=llm_config)
                                        
                                        # Create agent orchestrator
                                        agent_orchestrator = AgentOrchestrator(
                                            app_id=app_id,
                                            env=env,
                                            model_name=model_name,
                                            temperature=config.AGENT_TEMPERATURE
                                        )
                                        agent_orchestrator.initialize(
                                            kg_retriever=st.session_state.kg_retriever,
                                            original_documents="",  # Empty for Vespa-only mode
                                            vespa_wrapper=st.session_state.vespa_wrapper
                                        )
                                        st.session_state.agent_orchestrator = agent_orchestrator
                                        st.session_state.agent_state = AgentState()
                                        
                                        st.success("Agent initialized with Vespa!")
                                    except Exception as e:
                                        st.error(f"Failed to initialize agent: {str(e)}")
                            else:
                                # Test failed
                                st.error(f"**Vespa Connection Test Failed**\n\n{test_result.get('error', 'Unknown error')}")
                                if test_result.get('suggestion'):
                                    st.warning(test_result['suggestion'])
                                st.session_state.vespa_wrapper = None
                        else:
                            st.error("Failed to create Vespa wrapper")
                    except Exception as e:
                        st.error(f"Vespa connection error: {str(e)}")
                        st.info("Common issues: Invalid schema ID, wrong environment, or authentication problems")
            
            if st.session_state.vespa_wrapper:
                info = st.session_state.vespa_wrapper.get_schema_info()
                st.info(f"Connected: {info['schema_id']} ({info['env']})")
    
    st.markdown("---")
    
    # Agent Settings
    if config.ENABLE_AGENT_MODE:
        st.subheader("ReAct Agent")
        
        # Check if agent modules are available
        if not AGENT_MODULES_AVAILABLE:
            st.error(f"""
            **Agent modules not available**
            
            Error: {AGENT_IMPORT_ERROR}
            
            **Troubleshooting:**
            1. Ensure all agent files exist in: `{current_dir}`
            2. Required files:
               - `query_router.py`
               - `react_agent.py`
               - `agent_state.py`
               - `llm_adapter.py`
               - `agent_tools.py`
               - `prompts.py`
            3. Install dependencies: `pip install langgraph langchain langchain-core`
            4. Restart the Streamlit app
            """)
            enable_agent = False
        else:
            enable_agent = st.checkbox(
                "Enable Agent Mode",
                value=st.session_state.enable_agent,
                help="Use LangGraph ReAct agent for complex multi-step reasoning. Agent automatically engages for complex queries."
            )
        
        st.session_state.enable_agent = enable_agent
        
        if enable_agent:
            show_agent_trace = st.checkbox(
                "Show Reasoning Trace",
                value=st.session_state.show_agent_trace,
                help="Display the agent's reasoning steps and tool usage"
            )
            st.session_state.show_agent_trace = show_agent_trace
            
            # Agent Process Flow Diagram
            with st.expander("How Agent-LLM Interaction Works"):
                st.markdown("""
                ### Agent-LLM Interaction Flow
                
                The agent uses your **same LLM multiple times** in an iterative pattern:
                
                ```
                USER QUERY
                    ↓
                ┌─────────────────────────────────────┐
                │ AGENT STARTS                        │
                │ (powered by your LLM)               │
                └─────────────────────────────────────┘
                    ↓
                ┌─────────────────────────────────────┐
                │ LLM CALL #1: Planning               │
                │ "What should I do first?"           │
                │ → "Use search_entities tool"        │
                └─────────────────────────────────────┘
                    ↓
                ┌─────────────────────────────────────┐
                │ TOOL EXECUTION                      │
                │ search_entities(pattern="AC-2")     │
                │ → Returns entity data               │
                └─────────────────────────────────────┘
                    ↓
                ┌─────────────────────────────────────┐
                │ LLM CALL #2: Interpret              │
                │ "Found AC-2. What next?"            │
                │ → "Use get_entity_relationships"    │
                └─────────────────────────────────────┘
                    ↓
                ┌─────────────────────────────────────┐
                │ TOOL EXECUTION                      │
                │ get_entity_relationships("AC-2")    │
                │ → Returns connected entities        │
                └─────────────────────────────────────┘
                    ↓
                ┌─────────────────────────────────────┐
                │ LLM CALL #3: Continue               │
                │ "Need more details. Use traverse"   │
                │ → "Use traverse_graph tool"         │
                └─────────────────────────────────────┘
                    ↓
                ┌─────────────────────────────────────┐
                │ TOOL EXECUTION                      │
                │ traverse_graph(depth=2)             │
                │ → Returns dependency tree           │
                └─────────────────────────────────────┘
                    ↓
                ┌─────────────────────────────────────┐
                │ LLM CALL #4: Synthesize             │
                │ "I have everything. Final answer:"  │
                │ → Comprehensive response            │
                └─────────────────────────────────────┘
                    ↓
                RESPONSE TO USER
                ```
                
                **Key Points:**
                - Same LLM used throughout (4-10+ calls per query)
                - Agent = LLM + Tools + Iterative Reasoning
                - Each LLM call: Plan → Execute Tool → Interpret → Repeat
                - Final LLM call synthesizes all gathered information
                
                **Simple Flow:** 1 LLM call  
                **Agent Flow:** 4-10+ LLM calls (more thorough!)
                """)
            
            if st.session_state.agent_state:
                with st.expander("View Agent Statistics"):
                    stats = st.session_state.agent_state.get_statistics()
                    st.json(stats)
        
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
                    documents_for_kg = []
                    
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
                                documents_for_kg.append({
                                    'name': uploaded_file.name,
                                    'content': content,
                                })
                            elif file_ext == 'json':
                                # Extract from JSON
                                content = json_extractor.extract_from_json_file(tmp_path, uploaded_file.name)
                                all_content.append(content)
                                
                                # Also load raw JSON for KG
                                with open(tmp_path, 'r', encoding='utf-8') as f:
                                    json_data = json.load(f)
                                documents_for_kg.append({
                                    'name': uploaded_file.name,
                                    'content': content,
                                    'json_data': json_data,
                                })
                            elif file_ext == 'jsonl':
                                # Extract from JSONL
                                content = json_extractor.extract_from_jsonl_file(tmp_path, uploaded_file.name)
                                all_content.append(content)
                                
                                # Also load raw JSONL for KG
                                with open(tmp_path, 'r', encoding='utf-8') as f:
                                    jsonl_data = [json.loads(line) for line in f if line.strip()]
                                documents_for_kg.append({
                                    'name': uploaded_file.name,
                                    'content': content,
                                    'json_data': jsonl_data,
                                })
                            elif file_ext == 'txt':
                                # Extract from text file
                                with open(tmp_path, 'r', encoding='utf-8') as f:
                                    text_content = f.read()
                                formatted_txt = f"\n\n{'='*80}\nDocument: {uploaded_file.name}\n{'='*80}\n\n{text_content}\n"
                                all_content.append(formatted_txt)
                                documents_for_kg.append({
                                    'name': uploaded_file.name,
                                    'content': text_content,
                                })
                        finally:
                            os.unlink(tmp_path)
                    
                    # Combine all extracted content
                    st.session_state.extracted_text = "\n\n".join(all_content)
                    
                    # Build Knowledge Graph if enabled
                    if use_kg:
                        with st.spinner("Building Knowledge Graph..."):
                            kg_retriever = KGRetriever()
                            kg_retriever.build_knowledge_graph(documents_for_kg)
                            st.session_state.kg_retriever = kg_retriever
                    
                    # Initialize LLM
                    llm_config = LLMConfig(
                        app_id=app_id,
                        env=env,
                        model_name=model_name,
                        temperature=temperature,
                        log_level=log_level,
                    )
                    st.session_state.llm = LLM.init(config=llm_config)
                    
                    # Initialize Agent if enabled
                    if config.ENABLE_AGENT_MODE and st.session_state.enable_agent and AGENT_MODULES_AVAILABLE:
                        if st.session_state.kg_retriever:
                            with st.spinner("Initializing ReAct Agent..."):
                                try:
                                    # Create query router
                                    st.session_state.query_router = QueryRouter(
                                        complexity_threshold=config.AGENT_COMPLEXITY_THRESHOLD
                                    )
                                    
                                    # Create agent orchestrator
                                    agent_orchestrator = AgentOrchestrator(
                                        app_id=app_id,
                                        env=env,
                                        model_name=model_name,
                                        temperature=config.AGENT_TEMPERATURE
                                    )
                                    agent_orchestrator.initialize(
                                        kg_retriever=st.session_state.kg_retriever,
                                        original_documents=st.session_state.extracted_text,
                                        vespa_wrapper=st.session_state.vespa_wrapper
                                    )
                                    st.session_state.agent_orchestrator = agent_orchestrator
                                    
                                    # Create agent state for session tracking
                                    st.session_state.agent_state = AgentState()
                                except Exception as e:
                                    st.error(f"Failed to initialize agent: {str(e)}")
                                    st.info(f"Current directory: {current_dir}")
                                    st.session_state.agent_orchestrator = None
                    
                    # Store file info
                    st.session_state.uploaded_files_info = [
                        {"name": f.name, "size": f.size} for f in uploaded_files
                    ]
                    
                    success_msg = f"Successfully processed {len(uploaded_files)} documents!"
                    if config.ENABLE_AGENT_MODE and st.session_state.agent_orchestrator:
                        success_msg += " Agent mode ready!"
                    st.success(success_msg)
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
    # Check if Vespa is available as fallback
    if st.session_state.vespa_wrapper and config.VESPA_AS_FALLBACK:
        st.success("""
        **Vespa Mode Enabled**
        
        No documents uploaded - using Vespa vector database for context.
        
        You can ask questions and the agent will search the Vespa DB for relevant information.
        """)
    else:
        st.info("""
        **Getting Started:**
        1. Configure your App ID and Environment in the sidebar
        2. Enable Knowledge Graph Enhancement for better responses (recommended)
        3. **Option A:** Upload documents (PDF, JSON, JSONL, or TXT) and click 'Process Documents'
        4. **Option B:** Enable and connect to Vespa Vector Store for broader knowledge base
        5. Start asking questions!
        
        **Knowledge Graph Benefits:**
        - Automatically extracts entities (controls, risks, assets, policies, etc.)
        - Identifies relationships between entities
        - Provides better context and linkage for more accurate responses
        - Enables comprehensive analysis of connected information
        
        **Vespa Vector Store:**
        - Access broader knowledge base beyond uploaded documents
        - Automatic fallback when no documents uploaded
        - Search with filters for specific domains
        
        **ReAct Agent Mode:**
        - Enable in sidebar for complex multi-step reasoning
        - Agent automatically activates for complex queries
        - Uses your LLM iteratively with 10 specialized tools (9 KG + 1 Vespa)
        - View "How Agent-LLM Interaction Works" in sidebar for details
        """)
# Allow chat if documents are loaded OR Vespa is connected
if st.session_state.extracted_text or (st.session_state.vespa_wrapper and config.VESPA_AS_FALLBACK):
    # Show ready message with KG stats
    if st.session_state.extracted_text:
        ready_message = f"Ready to chat! {len(st.session_state.uploaded_files_info)} documents loaded."
    else:
        ready_message = "Ready to chat! Using Vespa vector database for context."
    
    if st.session_state.use_kg and st.session_state.kg_retriever:
        kg_stats = st.session_state.kg_retriever.get_statistics()
        ready_message += f" | KG: {kg_stats['entity_count']} entities, {kg_stats['relationship_count']} relationships"
    st.success(ready_message)
    
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
        
        # Add mode badge if using agent
        mode_badge = ""
        if "Agent Reasoning:" in formatted_response:
            mode_badge = '<span style="background-color: #4caf50; color: white; padding: 2px 8px; border-radius: 3px; font-size: 0.8em; margin-bottom: 10px; display: inline-block;">Agent Mode</span><br><br>'
        elif config.ENABLE_AGENT_MODE and st.session_state.enable_agent:
            mode_badge = '<span style="background-color: #2196f3; color: white; padding: 2px 8px; border-radius: 3px; font-size: 0.8em; margin-bottom: 10px; display: inline-block;">Simple Mode</span><br><br>'
        
        st.markdown(f"""
        <div class="chat-message assistant-message">
            {mode_badge}{formatted_response}
        </div>
        """, unsafe_allow_html=True)
    
    # Chat input - always visible when documents are loaded or Vespa is connected
    if st.session_state.extracted_text:
        prompt = st.chat_input("Ask a question about your documents...")
    else:
        prompt = st.chat_input("Ask a question (using Vespa vector database)...")
    
    if prompt:
        # Display user message immediately
        st.session_state.chat_history.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "question": prompt,
            "response": "..."
        })
        
        with st.spinner("Generating response..."):
            try:
                # Determine if we should use agent
                use_agent_for_query = False
                routing_info = None
                
                if (config.ENABLE_AGENT_MODE and 
                    AGENT_MODULES_AVAILABLE and
                    st.session_state.enable_agent and 
                    st.session_state.agent_orchestrator and
                    st.session_state.query_router):
                    
                    use_agent_for_query, routing_info = st.session_state.query_router.should_use_agent(prompt)
                
                # Route to agent or simple flow
                if use_agent_for_query:
                    # Use ReAct Agent
                    with st.spinner(f"Agent analyzing (complexity: {routing_info['complexity_score']})..."):
                        agent_result = st.session_state.agent_orchestrator.query(
                            query=prompt,
                            include_trace=st.session_state.show_agent_trace,
                            state=st.session_state.agent_state
                        )
                        
                        actual_response = agent_result.get('response', 'No response generated')
                        
                        # Add routing info and trace if enabled
                        if st.session_state.show_agent_trace and agent_result.get('trace'):
                            trace_info = f"\n\n---\n**Agent Reasoning:**\n"
                            trace_info += f"- Query Type: {routing_info['query_type']}\n"
                            trace_info += f"- Complexity Score: {routing_info['complexity_score']}/100\n"
                            trace_info += f"- Iterations: {agent_result.get('iterations', 'N/A')}\n"
                            trace_info += f"- Routing Reason: {routing_info['routing_reason']}\n"
                            actual_response += trace_info
                
                # Build prompt based on whether KG is enabled
                elif st.session_state.use_kg and st.session_state.kg_retriever and st.session_state.extracted_text:
                    # Use Knowledge Graph enhanced prompt (simple flow)
                    full_prompt = st.session_state.kg_retriever.build_contextual_prompt(
                        prompt, 
                        st.session_state.extracted_text
                    )
                elif st.session_state.vespa_wrapper and not st.session_state.extracted_text:
                    # Use Vespa as fallback when no documents uploaded
                    vespa_result = st.session_state.vespa_wrapper.search(prompt, top_k=config.VESPA_TOP_K)
                    vespa_context = st.session_state.vespa_wrapper.format_results_for_llm(vespa_result)
                    
                    full_prompt = f"""You are a cybersecurity and risk analysis assistant with access to a vector database.

{vespa_context}

Question: {prompt}

Instructions:
1. Use the Vespa search results above to answer the question
2. Cite specific results when providing answers
3. If the results don't contain relevant information, state that clearly
4. Format your response professionally with bullet points and clear organization

Answer:"""
                else:
                    # Use traditional prompt
                    full_prompt = f"""You are a cybersecurity and risk analysis assistant. Your role is to help users understand security controls, compliance requirements, risk assessments, and related governance documentation.

The documents may contain:
- Security controls and compliance frameworks
- Risk assessment data and audit findings
- Policy documents and governance standards
- Tables with control mappings, risk metrics, or compliance data
- Structured JSON/JSONL with control definitions, asset types, or security configurations
- Regular text describing security procedures and requirements

Document Content:
{st.session_state.extracted_text if st.session_state.extracted_text else "No documents uploaded."}

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
                
                # Only invoke LLM if not using agent (agent already provided response)
                if not use_agent_for_query:
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

