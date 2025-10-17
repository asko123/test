# Vespa Vector Store Integration

## Overview

The ReAct Agent now includes Vespa vector database search as an additional tool, providing access to a broader knowledge base beyond uploaded documents. Vespa can be used:

1. **As an agent tool** - The agent can search Vespa when it needs additional context
2. **As a fallback** - Automatically used when no documents are uploaded
3. **For enrichment** - Combined with document knowledge for comprehensive answers

---

## Features

### Agent Tool Integration
- **search_vespa_db** tool added to agent's toolkit (10th tool)
- Agent can call Vespa search during multi-step reasoning
- Results formatted and integrated into agent's analysis

### Automatic Fallback
- When no documents uploaded, Vespa becomes primary knowledge source
- Agent can still operate using Vespa for context
- Seamless user experience

### Flexible Configuration
- Schema ID configurable
- Environment selectable (dev, uat, prod)
- Top-K results configurable
- Optional filters support

---

## Configuration

### In `config.py`

```python
# Vespa Vector Store Configuration
ENABLE_VESPA_SEARCH = True           # Enable/disable Vespa
VESPA_SCHEMA_ID = "tech_risk_ai"     # Vespa schema ID
VESPA_ENV = "uat"                    # Environment (dev, uat, prod)
VESPA_TOP_K = 10                     # Results to retrieve
VESPA_AS_FALLBACK = True             # Use when no documents
```

---

## Usage

### Streamlit App

#### Step 1: Configure Vespa (Sidebar)
1. Check "Enable Vespa Search"
2. Enter Schema ID (default: `tech_risk_ai`)
3. Select Environment (dev/uat/prod)
4. Click "Connect to Vespa"
5. Wait for success message

#### Step 2: Use with Documents
- Upload documents as usual
- Vespa available as additional tool for agent
- Agent uses Vespa when it needs broader context

#### Step 3: Use Without Documents
- Don't upload any documents
- Just connect to Vespa
- Ask questions directly
- Agent searches Vespa for answers

### Jupyter Notebook

#### Configure in Cell 5
```python
# Vespa Settings
enable_vespa_toggle.value = True
vespa_schema_input.value = 'tech_risk_ai'
vespa_env_selector.value = 'uat'
```

#### Initialize in Cell 15
Vespa automatically initializes when you run cell 15:
```
Connecting to Vespa Vector Store...
✓ Vespa connected: tech_risk_ai (uat)
```

---

## Vespa Tool Usage

### The Agent Can Use Vespa

When enabled, the agent has access to `search_vespa_db` tool:

```python
@tool
def search_vespa_db(
    query: str,
    top_k: int = 10,
    filters_json: Optional[str] = None
) -> str:
    """
    Search Vespa vector database for additional context.
    
    Examples:
    - search_vespa_db(query="What is the ingestion demo?", 
                     filters_json='{"field_1_s": "demo"}')
    - search_vespa_db(query="apple's net earning in 2024 Q3", 
                     top_k=10)
    """
```

### Agent Decision Making

The agent decides when to use Vespa:

**Scenario 1: No documents uploaded**
```
Query: "What is the ingestion demo?"
Agent thinks: "No documents available, I'll search Vespa"
Agent uses: search_vespa_db(query="ingestion demo")
```

**Scenario 2: Documents don't have info**
```
Query: "What is apple's net earning in 2024 Q3?"
Agent thinks: "Checked documents, no info found. Try Vespa"
Agent uses: search_vespa_db(query="apple's net earning 2024 Q3")
```

**Scenario 3: Enrichment**
```
Query: "Compare our controls with industry standards"
Agent thinks: "I have controls from documents, need industry standards"
Agent uses: search_vespa_db(query="industry security control standards")
```

---

## API Examples

### Basic Search
```python
from vespa_search import create_vespa_wrapper

# Create wrapper
vespa = create_vespa_wrapper(schema_id="tech_risk_ai", env="uat")

# Simple search
result = vespa.search("What is the ingestion demo?", top_k=10)
print(result)
```

### Search with Filters
```python
# Search with filters
result = vespa.search(
    query="What is the ingestion demo?",
    filters={"field_1_s": "demo"}
)
```

### Formatted for LLM
```python
# Get results formatted for LLM
formatted = vespa.format_results_for_llm(result)
print(formatted)
```

---

## Architecture

### Tool Flow

```
Agent receives query
    ↓
Agent decides tools needed
    ↓
    ├─ Knowledge Graph tools (if documents uploaded)
    │   - search_entities
    │   - get_entity_relationships
    │   - traverse_graph
    │   └─ etc.
    │
    └─ Vespa tool (if Vespa connected)
        - search_vespa_db
            ↓
        Searches vector database
            ↓
        Returns formatted results
            ↓
        Agent synthesizes with other results
```

### Fallback Logic

```
User asks question
    ↓
Documents uploaded? 
    ├─ YES → Use documents + KG + Vespa (if enabled)
    └─ NO  → 
        ↓
    Vespa connected?
        ├─ YES → Use Vespa as primary source
        └─ NO  → Show "please upload documents" message
```

---

## Benefits

### 1. Broader Knowledge Base
- Access to Vespa's full vector database
- Not limited to uploaded documents
- Can answer questions about data not in documents

### 2. Flexible Operation
- Works with or without documents
- Vespa as fallback ensures always functional
- Combines document and vector search

### 3. Agent Enhancement
- Agent can search both sources
- Makes intelligent decisions about which to use
- Synthesizes information from multiple sources

### 4. User Convenience
- No need to upload documents for general queries
- Can start asking questions immediately
- Documents add specific context when needed

---

## Example Queries

### With Documents + Vespa

**Query:** "How do our uploaded controls compare to industry standards?"

**Agent reasoning:**
1. Uses `search_entities` to find controls in uploaded documents
2. Uses `search_vespa_db` to find industry standards in Vespa
3. Compares and synthesizes comprehensive answer

### Without Documents (Vespa Only)

**Query:** "What is apple's net earning in 2024 Q3?"

**Agent reasoning:**
1. Detects no documents available
2. Uses `search_vespa_db` to search Vespa
3. Returns results from vector database

**Query:** "What is the ingestion demo?"

**Agent reasoning:**
1. Uses `search_vespa_db(query="ingestion demo", filters={"field_1_s": "demo"})`
2. Returns relevant demo information

---

## Configuration Examples

### Streamlit

```python
# In sidebar
Schema ID: tech_risk_ai
Environment: uat
[Connect to Vespa] button clicked
→ "Connected to Vespa: tech_risk_ai (uat)"
```

### Notebook

```python
# Cell 5
enable_vespa_toggle.value = True
vespa_schema_input.value = 'tech_risk_ai'
vespa_env_selector.value = 'uat'

# Cell 15 auto-connects
# Output: "✓ Vespa connected: tech_risk_ai (uat)"
```

---

## Troubleshooting

### Issue: "Vespa connection failed"

**Causes:**
1. Invalid schema ID
2. Wrong environment
3. Network issues
4. goldmansachs package not available

**Solution:**
```python
# Verify package
python -c "from goldmansachs.awm_genai import VectorStore; print('OK')"

# Check schema ID
# Ensure "tech_risk_ai" exists in your environment

# Try different environment
# Switch between dev/uat/prod
```

### Issue: "Agent not using Vespa tool"

**Causes:**
1. Vespa not initialized
2. Agent determined it's not needed
3. Error in Vespa connection

**Solution:**
- Check "Connected to Vespa" message appears
- Enable reasoning trace to see agent's decisions
- Ask query that clearly needs Vespa (e.g., about data not in documents)

### Issue: Search returns no results

**Possible:**
1. Query doesn't match Vespa data
2. Filters too restrictive
3. Schema has no data for query

**Try:**
- Broader query without filters
- Different search terms
- Check Vespa schema has relevant data

---

## Advanced Usage

### Custom Filters

```python
# Agent can use filters
search_vespa_db(
    query="security controls",
    filters_json='{"domain": "cybersecurity", "year": "2024"}'
)
```

### Pagination

```python
# Search with pagination
result = vespa.search(query="controls", top_k=20, page=2)
```

### Combined with KG

Agent intelligently combines:
1. Documents → Extracts entities with KG
2. Vespa → Gets broader context
3. Synthesizes → Comprehensive answer using both

---

## Security Considerations

- Vespa connection uses same auth as LLM (goldmansachs package)
- Schema access controlled by environment (dev/uat/prod)
- Only accesses configured schema
- No data written to Vespa (read-only)

---

## Summary

**New Capability:** 10th Agent Tool  
**Tool Name:** `search_vespa_db`  
**Purpose:** Access broader knowledge base via Vespa vector database  
**Availability:** Streamlit app + Jupyter notebook  
**Automatic Fallback:** Yes (when no documents uploaded)  
**Integration:** Seamless with existing agent and KG tools  

**The agent can now search both your documents AND the Vespa database for the most comprehensive answers!**

