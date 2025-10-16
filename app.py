"""
Streamlit App for Document Chat Bot
Multi-document chat interface for PDF documents
Enhanced with LangGraph ReAct Agent capabilities
"""

import streamlit as st
from goldmansachs.awm_genai import LLM, LLMConfig
import config
from datetime import datetime
import tempfile
import os
import json
from pdf_extractor import PDFExtractor
from json_extractor import JSONExtractor
from kg_retriever import KGRetriever
from query_router import QueryRouter
from react_agent import AgentOrchestrator
from agent_state import AgentState

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
    
    # Agent Settings
    if config.ENABLE_AGENT_MODE:
        st.subheader("ReAct Agent")
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
                    if config.ENABLE_AGENT_MODE and st.session_state.enable_agent:
                        if st.session_state.kg_retriever:
                            with st.spinner("Initializing ReAct Agent..."):
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
                                    original_documents=st.session_state.extracted_text
                                )
                                st.session_state.agent_orchestrator = agent_orchestrator
                                
                                # Create agent state for session tracking
                                st.session_state.agent_state = AgentState()
                    
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
    st.info("""
    **Getting Started:**
    1. Configure your App ID and Environment in the sidebar
    2. Enable Knowledge Graph Enhancement for better responses (recommended)
    3. Upload one or more documents (PDF, JSON, JSONL, or TXT)
    4. Click 'Process Documents' to extract text and build the knowledge graph
    5. Start asking questions about your documents
    
    **Knowledge Graph Benefits:**
    - Automatically extracts entities (controls, risks, assets, policies, etc.)
    - Identifies relationships between entities
    - Provides better context and linkage for more accurate responses
    - Enables comprehensive analysis of connected information
    
    **ReAct Agent Mode:**
    - Enable in sidebar for complex multi-step reasoning
    - Agent automatically activates for complex queries
    - Uses your LLM iteratively with 9 specialized tools
    - View "How Agent-LLM Interaction Works" in sidebar for details
    """)
else:
    # Show ready message with KG stats
    ready_message = f"Ready to chat! {len(st.session_state.uploaded_files_info)} documents loaded."
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
                # Determine if we should use agent
                use_agent_for_query = False
                routing_info = None
                
                if (config.ENABLE_AGENT_MODE and 
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
                elif st.session_state.use_kg and st.session_state.kg_retriever:
                    # Use Knowledge Graph enhanced prompt (simple flow)
                    full_prompt = st.session_state.kg_retriever.build_contextual_prompt(
                        prompt, 
                        st.session_state.extracted_text
                    )
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

