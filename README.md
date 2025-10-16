# Document Chat Bot with Knowledge Graph Enhancement

A multi-document chatbot for querying PDF, JSON, JSONL, and text documents with advanced Knowledge Graph capabilities and intelligent ReAct agent for complex multi-step reasoning.

## Features

###  Core Features
- **Multi-Format Support**: PDF, JSON, JSONL, and TXT documents
- **Interactive Chat Interface**: Streamlit-based web UI
- **Multiple LLM Models**: Gemini 2.5 Pro and Flash Lite
- **Multi-Document Processing**: Handle up to 10 documents simultaneously

###  Knowledge Graph Enhancement
- **Automatic Entity Extraction**: Identifies controls, risks, assets, policies, requirements, people, and standards
- **Relationship Detection**: Discovers connections between entities (implements, mitigates, requires, etc.)
- **Context-Aware Responses**: Leverages entity relationships for better, more connected answers
- **Query Intent Analysis**: Automatically detects query type (list, explain, relationship, compliance, impact)
- **Graph Statistics**: View entity and relationship metrics in real-time

###  LangGraph ReAct Agent (NEW!)
- **Intelligent Query Routing**: Automatically detects complex queries and routes to agent
- **Multi-Step Reasoning**: Breaks down complex questions into sequential tool calls
- **Tool-Based Analysis**: 9 specialized tools for KG operations and document search
- **Self-Correcting**: Agent iterates and refines approach based on results
- **Transparent Reasoning**: Optional display of agent's thinking process and tool usage
- **Advanced Capabilities**: 
  - Multi-hop relationship traversal
  - Impact analysis across dependencies
  - Compliance gap detection
  - Comparative framework analysis

###  Extracted Entity Types
- **CONTROL**: Security controls (AC-2, ISO-27001-A.9.2.1, etc.)
- **RISK**: Risk identifiers and severity levels
- **ASSET**: IT assets (servers, databases, applications)
- **REQUIREMENT**: Compliance requirements and mandates
- **POLICY**: Security and organizational policies
- **PERSON**: Responsible parties, owners, managers
- **STANDARD**: Frameworks (NIST, ISO, SOC, PCI, HIPAA, GDPR)

## Quick Start

### Prerequisites
- Python 3.8+
- Valid App ID and credentials

### Installation

1. Run setup script:
```bash
./setup.sh
source venv/bin/activate
```

2. Configure credentials in `config.py`:
```python
APP_ID = "your_app_id"
ENV = "uat"  # or "prod"
```

## Running the Application

### Option 1: Streamlit Web App

```bash
streamlit run app.py
```

Then:
1. Configure App ID and Environment in sidebar
2. Enable Knowledge Graph Enhancement (recommended)
3. **(Optional)** Enable Agent Mode for complex reasoning capabilities
4. Upload documents (PDF, JSON, JSONL, or TXT)
5. Click "Process Documents" to build the knowledge graph
6. Start chatting - agent automatically engages for complex queries!

### Option 2: Jupyter Notebook (Continuous Chat)

```bash
jupyter notebook chatbot.ipynb
```

**NEW! Continuous Chat Mode:**
1. Run setup cells (1-4)
2. Upload documents once (cell 9)
3. Initialize chat with Knowledge Graph (cell 15)
4. Start continuous chat loop (cell 17) - ask unlimited questions
5. Type `exit()` to stop chatting

See `NOTEBOOK_GUIDE.md` for detailed instructions.

### Option 3: Python Script

```python
from document_processor import DocumentProcessor
from llm_handler import LLMHandler

# Initialize
doc_processor = DocumentProcessor(app_id="trai", env="uat")
llm_handler = LLMHandler(app_id="trai", env="uat", model_name="gemini-2.0-flash")

# Upload documents
documents = doc_processor.upload_documents(["doc1.pdf", "doc2.pdf"])

# Query
response = llm_handler.query("What are the key findings?", documents=documents)
print(response)
```

## Configuration

Edit `config.py`:

```python
APP_ID = "trai"
ENV = "uat"
DEFAULT_MODEL = "gemini-2.0-flash"
DEFAULT_TEMPERATURE = 0
```

## Files

### Core Application
- `app.py` - Streamlit web app with KG integration
- `config.py` - Application configuration
- `chatbot.ipynb` - Jupyter notebook interface

### Document Processing
- `document_processor.py` - Document upload and management
- `pdf_extractor.py` - PDF text extraction
- `json_extractor.py` - JSON/JSONL data extraction

### LLM Integration
- `llm_handler.py` - LLM interaction handler

### Knowledge Graph
- `knowledge_graph.py` - Core KG module with entity/relationship extraction
- `kg_retriever.py` - Enhanced retrieval system using KG
- `test_kg.py` - KG test suite

### ReAct Agent (NEW!)
- `llm_adapter.py` - LangChain adapter for Goldman Sachs LLM
- `agent_tools.py` - Tool definitions for agent (9 specialized tools)
- `query_router.py` - Intelligent routing between simple and agent flows
- `react_agent.py` - LangGraph ReAct agent implementation
- `prompts.py` - Agent system prompts and instructions
- `agent_state.py` - State and memory management
- `test_agent.py` - Agent test suite

### Documentation
- `README.md` - This file
- `KG_IMPLEMENTATION_GUIDE.md` - Detailed KG implementation guide
- `IMPLEMENTATION_SUMMARY.md` - Project implementation summary
- `langgraph-react-integration.plan.md` - Agent integration plan

## Knowledge Graph Usage

### Benefits
1. **Better Context**: Entities and relationships tracked across documents
2. **Improved Accuracy**: More precise answers with entity recognition
3. **Enhanced Analysis**: Can answer "how are X and Y connected?" questions
4. **Structured Information**: Organized entities and categorized relationships

### Example Queries

**Without KG:**
```
Q: What controls address database security?
A: Basic text search results...
```

**With KG:**
```
Q: What controls address database security?
A: 
- Control AC-2 (Account Management) - APPLIES_TO Database_Server
- Control AU-2 (Audit Events) - MITIGATES Database_Access_Risk
- Connected to Requirement REQ-123 and Standard NIST_SP_800-53
```

### Testing the Knowledge Graph

Run the test suite:
```bash
python test_kg.py
```

All 7 tests should pass:
- Entity Extraction from Text
- Entity Extraction from JSON
- Relationship Detection
- Knowledge Graph Building
- Query Context Retrieval
- KG Retriever Integration
- Contextual Prompt Building

## ReAct Agent Usage

### What is the ReAct Agent?

The ReAct Agent is an intelligent reasoning system powered by LangGraph that can:
- **Think step-by-step** through complex queries
- **Use tools** to gather information from the knowledge graph
- **Self-correct** by trying different approaches if initial results are insufficient
- **Explain its reasoning** showing you how it arrived at an answer

### When Does the Agent Activate?

The system automatically routes queries to the agent based on complexity:

**Simple Queries → Direct KG Retrieval:**
- "What is AC-2?"
- "List all controls"
- "Show me high-severity risks"

**Complex Queries → ReAct Agent:**
- "How does AC-2 relate to ISO 27001 and NIST compliance?"
- "What would be impacted if we remove control AC-2?"
- "Which high-severity risks lack mitigation controls?"
- "Compare controls across ISO 27001 and NIST frameworks"

### Agent Tools

The agent has access to 9 specialized tools:

1. **search_entities** - Find entities by type and pattern
2. **get_entity_details** - Get complete info about an entity
3. **get_entity_relationships** - Discover connections
4. **find_relationship_path** - Find how two entities connect
5. **search_documents** - Search original document content
6. **aggregate_entity_info** - Summarize multiple entities
7. **detect_compliance_gaps** - Find missing controls/requirements
8. **traverse_graph** - Deep graph exploration
9. **query_kg_statistics** - Get graph metrics

### Example: Agent in Action

**Query:** "What would be impacted if we remove control AC-2?"

**Agent Reasoning:**
1. Searches for entity "AC-2" (uses `search_entities`)
2. Gets all relationships for AC-2 (uses `get_entity_relationships`)
3. Traverses dependency graph (uses `traverse_graph`)
4. Aggregates impacted entities (uses `aggregate_entity_info`)
5. Synthesizes comprehensive impact report

**Response:** Detailed breakdown of:
- Directly affected entities (risks, assets, requirements)
- Downstream impacts (dependent controls, policies)
- Compliance gaps that would result
- Recommended mitigation strategies

### Configuring the Agent

Edit `config.py` to customize agent behavior:

```python
# Enable/disable agent mode
ENABLE_AGENT_MODE = True

# Complexity threshold (0-100) to trigger agent
AGENT_COMPLEXITY_THRESHOLD = 60

# Maximum reasoning iterations
AGENT_MAX_ITERATIONS = 10

# Show reasoning trace in UI
SHOW_AGENT_REASONING = True
```

### Testing the Agent

Run the agent test suite:
```bash
python test_agent.py
```

Tests include:
- Query routing logic
- Complexity scoring
- Agent state management
- Tool functionality
- End-to-end integration

## Advanced Configuration

### Customize Entity Patterns

Edit `knowledge_graph.py` to add custom entity types:
```python
ENTITY_PATTERNS['CUSTOM_TYPE'] = [
    r'your_pattern_here',
]
```

### Adjust Relationship Detection

Modify relationship detection in `knowledge_graph.py`:
- Change proximity threshold (default: 200 chars)
- Add new relationship patterns
- Adjust confidence scoring

## Troubleshooting

### Knowledge Graph Issues

**No entities extracted:**
- Check if documents contain recognizable patterns
- Add custom patterns for your specific domain

**Too many false positives:**
- Make entity patterns more specific
- Increase context validation window

**Missing relationships:**
- Adjust proximity threshold
- Add more relationship indicator patterns

## Performance

### Typical Metrics
- Entity extraction: ~100-500 entities per document
- Relationship detection: ~200-1000 relationships
- Processing time: 2-5 seconds per document
- Memory usage: ~20-50MB for KG

## Requirements

See `requirements.txt`:
- streamlit>=1.28.0
- goldmansachs.awm_genai
- pdfplumber>=0.10.0
- networkx>=3.1 (for Knowledge Graph)
- matplotlib>=3.7.0 (for visualizations)
- langgraph>=0.0.20 (for ReAct Agent)
- langchain>=0.1.0 (for agent tools)
- langchain-core>=0.1.0 (for LLM integration)

## Additional Documentation

- **KG Implementation Guide**: See `KG_IMPLEMENTATION_GUIDE.md` for detailed KG documentation
- **API Reference**: See implementation guide for API details
- **Implementation Summary**: See `IMPLEMENTATION_SUMMARY.md` for project overview

