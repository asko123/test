# ReAct Agent Quick Start Guide

## Getting Started in 3 Minutes

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Application
```bash
streamlit run app.py
```

### 3. Enable Agent Mode
In the Streamlit sidebar:
1. Check ✅ "Enable Agent Mode"
2. (Optional) Check ✅ "Show Reasoning Trace"

### 4. Upload Documents & Chat
1. Upload your documents (PDF, JSON, JSONL, or TXT)
2. Click "Process Documents"
3. Start asking questions!

---

## How It Works

The system automatically routes your queries:

### Simple Questions → Fast Direct Answers
- "What is AC-2?"
- "List all controls"
- "Show me high risks"

**Response time:** 2-3 seconds  
**Mode:** ⚡ Simple Mode

### Complex Questions → Agent Reasoning
- "How does AC-2 relate to ISO 27001 and NIST?"
- "What would be impacted if we remove AC-2?"
- "Which high risks lack mitigation controls?"

**Response time:** 5-15 seconds  
**Mode:** 🤖 Agent Mode

---

## Agent Tools Available

The agent can use these 9 tools:

1. **search_entities** - Find specific entities
2. **get_entity_details** - Get full info
3. **get_entity_relationships** - Find connections
4. **find_relationship_path** - Trace paths
5. **search_documents** - Search text
6. **aggregate_entity_info** - Summarize
7. **detect_compliance_gaps** - Find gaps
8. **traverse_graph** - Deep exploration
9. **query_kg_statistics** - Get metrics

---

## Example Queries

### Impact Analysis
```
Query: What would be affected if we remove control AC-2?

Agent will:
✓ Find AC-2 entity
✓ Get all relationships
✓ Traverse dependency graph
✓ Aggregate impact info
✓ Provide comprehensive report
```

### Gap Analysis
```
Query: Which high-severity risks don't have mitigation controls?

Agent will:
✓ Find all high-severity risks
✓ Check for MITIGATES relationships
✓ Identify gaps
✓ Provide prioritized list
```

### Compliance Mapping
```
Query: How do our controls map to both ISO 27001 and NIST 800-53?

Agent will:
✓ Find both standards
✓ Map controls to each
✓ Create coverage matrix
✓ Identify gaps
```

---

## Configuration

Edit `config.py`:

```python
# Enable/disable agent
ENABLE_AGENT_MODE = True

# When to use agent (0-100)
AGENT_COMPLEXITY_THRESHOLD = 60  # Lower = more agent use

# Max reasoning steps
AGENT_MAX_ITERATIONS = 10

# Show agent thinking
SHOW_AGENT_REASONING = True
```

---

## Troubleshooting

### Agent not activating?
→ Lower `AGENT_COMPLEXITY_THRESHOLD` to 40

### Agent too slow?
→ Reduce `AGENT_MAX_ITERATIONS` to 5  
→ Disable reasoning trace

### Want more agent use?
→ Lower `AGENT_COMPLEXITY_THRESHOLD` to 40-50

### Want less agent use?
→ Raise `AGENT_COMPLEXITY_THRESHOLD` to 70-80

---

## Testing

Run the test suite:
```bash
python test_agent.py
```

Expected output:
```
✓ Query routing logic
✓ Complexity scoring
✓ Agent state management
✓ Tool functionality
✓ Integration tests
```

---

## Need Help?

- **Full documentation:** See `README.md`
- **Implementation details:** See `AGENT_IMPLEMENTATION_SUMMARY.md`
- **Original plan:** See `langgraph-react-integration.plan.md`
- **How it works:** See `HOW_IT_WORKS.md`

---

**Ready to use!** 🚀

