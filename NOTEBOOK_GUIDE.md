# Jupyter Notebook Chat Guide

## Overview

The `chatbot.ipynb` notebook provides a streamlined, continuous chat interface for interacting with your documents. After uploading documents once, you can ask unlimited questions until you type `exit()`.

##  Step-by-Step Instructions

### 1. Setup (Run Once)

**Cells 1-4: Install and Configure**
```python
# Run these cells to:
# - Install required packages (including Knowledge Graph dependencies)
# - Import libraries
# - Configure app settings
# - Select your LLM model
```

### 2. Upload Documents (Run Once per Session)

**Cell 9: Upload and Extract**
```python
# 1. Click the file upload button
# 2. Select your documents (PDF, JSON, JSONL, or TXT)
# 3. Click "Extract Text" button
# 4. Wait for extraction to complete
```

**Supported Formats:**
- PDF files with text, tables, and embedded JSON
- JSON files (single object or array)
- JSONL files (one JSON object per line)
- Plain text files

### 3. Initialize Chat (Run Once per Session)

**Cell 15: Build Knowledge Graph**
```python
# This cell will:
# - Build a Knowledge Graph from your documents
# - Extract entities (controls, risks, assets, policies, etc.)
# - Detect relationships between entities
# - Initialize the chat interface
```

**Expected Output:**
```
Building Knowledge Graph for enhanced responses...
 Knowledge Graph built: 347 entities, 892 relationships

[SUCCESS] Interactive chat interface ready!
Documents loaded: security_policy.pdf, risk_assessment.json
 Knowledge Graph enhancement: ENABLED
================================================================================
You can now chat with your documents!
Type your questions and press Enter.
Type 'exit()' to stop chatting.
Type 'history' to view chat history.
================================================================================
```

### 4. Start Continuous Chat

**Cell 17: Chat Loop**
```python
# Run this cell to start chatting
# The loop will continue until you type 'exit()'
```

**Example Session:**
```
 Chat started! Ask your questions below.

 You: What security controls are mentioned?
 Thinking...
 Assistant:
================================================================================
Based on the documents, the following security controls are mentioned:

1. **AC-2 (Account Management)**
   - Source: security_policy.pdf, Page 3
   - Mitigates: Unauthorized access risk (R-001)
   - Applies to: Database servers, Application servers
   
2. **AU-2 (Audit Events)**
   - Source: security_policy.pdf, Page 5
   - Purpose: Monitor and log security events
   - Related to: NIST SP 800-53

[... full response ...]
================================================================================

 You: How are these controls related to ISO 27001?
 Thinking...
 Assistant:
================================================================================
[... response with relationships ...]
================================================================================

 You: exit()
 Exiting chat. Thank you!
Total questions asked: 2

 Session Summary:
  - Questions asked: 2
  - Documents processed: 2
  - Entities in KG: 347
  - Relationships in KG: 892
```

##  Chat Commands

During the chat session (Cell 17), you can use:

| Command | Description |
|---------|-------------|
| `[Your question]` | Ask any question about your documents |
| `exit()` or `quit()` | End the chat session |
| `history` | View quick summary of chat history |
| `Ctrl+C` | Interrupt the chat (then type exit() to quit) |

##  View Chat History

**Cell 19: Full History View**

Run this cell anytime (even after ending the chat) to see:
- Complete questions and answers
- Timestamps for each interaction
- Exportable DataFrame format
- Statistics (total questions, average response length, etc.)

##  Knowledge Graph Benefits

The notebook automatically builds a Knowledge Graph that:

### Entity Extraction
- **CONTROL**: Security controls (AC-2, AU-2, ISO-27001-A.9.2.1)
- **RISK**: Risk identifiers and severity levels
- **ASSET**: IT assets (servers, databases, applications)
- **REQUIREMENT**: Compliance requirements
- **POLICY**: Policies and procedures
- **PERSON**: Responsible parties, owners
- **STANDARD**: Frameworks (NIST, ISO, SOC, PCI, etc.)

### Relationship Detection
- **IMPLEMENTS**: Control implements requirement
- **MITIGATES**: Control mitigates risk
- **REQUIRES**: Dependencies between entities
- **OWNS**: Ownership relationships
- **APPLIES_TO**: Applicability relationships
- **RELATES_TO**: General relationships

### Enhanced Responses
- Better context from entity relationships
- More accurate answers with entity recognition
- Comprehensive coverage through relationship traversal
- Precise source attribution

##  Troubleshooting

### Issue: Knowledge Graph not building
**Solution:** 
- Check if `knowledge_graph.py` and `kg_retriever.py` are in the same directory
- Run: `%pip install networkx matplotlib -q`
- If KG fails, the notebook will fallback to standard mode

### Issue: Chat doesn't stop
**Solution:**
- Type exactly `exit()` or `quit()`
- Press Ctrl+C to interrupt, then type `exit()`

### Issue: Empty responses
**Solution:**
- Make sure you ran Cell 9 to extract document text
- Check that documents were uploaded successfully
- Verify LLM is initialized (Cell 7)

### Issue: "Not in globals" warning
**Solution:**
- Run cells in order: 1-4 → 9 → 15 → 17
- Don't skip Cell 15 (chat initialization)

##  Tips for Best Results

1. **Upload Quality Documents**: Clear, well-formatted documents work best
2. **Specific Questions**: Ask specific questions rather than broad ones
3. **Use Entity Names**: Mention specific controls, risks, or assets if known
4. **Ask Follow-ups**: The chat maintains context, so ask related follow-ups
5. **Check History**: Use `history` command to see previous Q&A
6. **View Full History**: Run Cell 19 to export chat history

##  Example Questions

### List Queries
- "What security controls are in the documents?"
- "List all high-severity risks"
- "Show me all database-related assets"

### Relationship Queries
- "How is control AC-2 related to database security?"
- "What controls mitigate unauthorized access?"
- "Which requirements does control AU-2 implement?"

### Compliance Queries
- "Which controls satisfy NIST SP 800-53?"
- "What are the ISO 27001 requirements?"
- "Show compliance mapping for access controls"

### Analysis Queries
- "What would be affected if we remove control AC-2?"
- "What assets are protected by access controls?"
- "Which policies apply to database servers?"

##  Restarting a Session

To start a new session with different documents:

1. **Restart Kernel**: Kernel → Restart Kernel
2. **Run Setup**: Execute cells 1-4 again
3. **Upload New Documents**: Use Cell 9
4. **Initialize Chat**: Run Cell 15
5. **Start Chatting**: Run Cell 17

##  Exporting Results

The chat history can be exported in multiple ways:

1. **Copy from Cell Output**: Select and copy from Cell 17 output
2. **DataFrame Export**: Run Cell 19, then export the DataFrame
3. **Programmatic Access**: Access `chat_history` variable directly

```python
# Export to JSON
import json
with open('chat_history.json', 'w') as f:
    json.dump(chat_history, f, indent=2)

# Export to CSV
import pandas as pd
df = pd.DataFrame(chat_history)
df.to_csv('chat_history.csv', index=False)
```

##  Summary

This notebook provides a **one-upload, continuous-chat** experience:
1. Upload documents **once**
2. Chat **unlimited times**
3. Stop **when you want** with `exit()`
4. View **complete history** anytime

No need to re-upload or reinitialize between questions - just keep chatting!

