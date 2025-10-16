# Agent-LLM Interaction Flow - Visual Guide

## Complete Process Flow Diagram

This document explains exactly how the ReAct Agent and LLM interact during query processing.

---

## 🎯 The Key Concept

**The agent DOES use the LLM - in fact, it uses it MULTIPLE times per query!**

The agent is NOT separate from the LLM. The agent IS the LLM being used in an intelligent, iterative way with tools.

---

## 📊 Visual Flow: Complex Query Example

```
USER QUERY: "What would be impacted if we remove control AC-2?"
│
│  ┌───────────────────────────────────────────────────────────────┐
│  │ QUERY ROUTER (query_router.py)                                │
│  │ Analyzes: Complexity Score = 75/100                           │
│  │ Decision: Route to AGENT (complex query detected)             │
│  └───────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────┐
│ STREAMLIT APP (app.py:433)                                      │
│ agent_orchestrator.query(prompt)                                │
└─────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────┐
│ REACT AGENT (react_agent.py:84)                                 │
│ self.agent.invoke({"messages": messages})                       │
│                                                                  │
│ This triggers LangGraph's create_react_agent                     │
│ which will call the LLM multiple times ↓                         │
└─────────────────────────────────────────────────────────────────┘
│
▼
┌═════════════════════════════════════════════════════════════════┐
║ 🧠 LLM CALL #1: PLANNING                                        ║
║ ─────────────────────────────────────────────────────────────── ║
║ File: llm_adapter.py, Line: 149                                 ║
║ Code: response = self._llm.invoke(prompt)                       ║
║                                                                  ║
║ LLM Receives:                                                    ║
║ - System prompt (defines agent role and capabilities)           ║
║ - Tool descriptions (9 tools with usage instructions)           ║
║ - User query: "What would be impacted if we remove AC-2?"       ║
║                                                                  ║
║ LLM Thinks:                                                      ║
║ "To analyze impact, I first need to find the AC-2 entity        ║
║  in the knowledge graph. I'll use the search_entities tool."    ║
║                                                                  ║
║ LLM Outputs:                                                     ║
║ {                                                                ║
║   "action": "search_entities",                                  ║
║   "action_input": {                                             ║
║     "value_pattern": "AC-2"                                     ║
║   }                                                              ║
║ }                                                                ║
╚═════════════════════════════════════════════════════════════════╝
│
▼
┌─────────────────────────────────────────────────────────────────┐
│ 🔧 TOOL EXECUTION #1                                            │
│ ─────────────────────────────────────────────────────────────── │
│ File: agent_tools.py                                            │
│ Tool: search_entities(value_pattern="AC-2")                     │
│                                                                  │
│ Executes:                                                        │
│ - Searches knowledge graph for entities matching "AC-2"         │
│ - Finds: CONTROL_AC-2 (Account Management)                      │
│                                                                  │
│ Returns:                                                         │
│ {                                                                │
│   "count": 1,                                                   │
│   "entities": [{                                                │
│     "id": "CONTROL_AC-2",                                       │
│     "type": "CONTROL",                                          │
│     "value": "AC-2",                                            │
│     "source": "security_policy.pdf"                             │
│   }]                                                             │
│ }                                                                │
└─────────────────────────────────────────────────────────────────┘
│
▼
┌═════════════════════════════════════════════════════════════════┐
║ 🧠 LLM CALL #2: INTERPRET & PLAN NEXT                          ║
║ ─────────────────────────────────────────────────────────────── ║
║ File: llm_adapter.py, Line: 149                                 ║
║ Code: response = self._llm.invoke(prompt)                       ║
║                                                                  ║
║ LLM Receives:                                                    ║
║ - Previous context (query + tool action + result)               ║
║ - Tool result: Found CONTROL_AC-2                               ║
║                                                                  ║
║ LLM Thinks:                                                      ║
║ "Good! I found AC-2. Now I need to find what's connected to     ║
║  it - what entities have relationships with AC-2? I'll use      ║
║  get_entity_relationships to find all connected entities."      ║
║                                                                  ║
║ LLM Outputs:                                                     ║
║ {                                                                ║
║   "action": "get_entity_relationships",                         ║
║   "action_input": {                                             ║
║     "entity_id": "CONTROL_AC-2",                                ║
║     "max_depth": 1                                              ║
║   }                                                              ║
║ }                                                                ║
╚═════════════════════════════════════════════════════════════════╝
│
▼
┌─────────────────────────────────────────────────────────────────┐
│ 🔧 TOOL EXECUTION #2                                            │
│ ─────────────────────────────────────────────────────────────── │
│ File: agent_tools.py                                            │
│ Tool: get_entity_relationships("CONTROL_AC-2", max_depth=1)    │
│                                                                  │
│ Executes:                                                        │
│ - Traverses graph to find all entities connected to AC-2        │
│ - Finds relationships: MITIGATES, IMPLEMENTS, APPLIES_TO        │
│                                                                  │
│ Returns:                                                         │
│ {                                                                │
│   "source_entity": "CONTROL_AC-2",                              │
│   "total_related": 12,                                          │
│   "relationships": [                                             │
│     {                                                            │
│       "related_id": "RISK_R-001",                               │
│       "related_type": "RISK",                                   │
│       "relationship_type": "MITIGATES",                         │
│       "direction": "outgoing"                                   │
│     },                                                           │
│     {                                                            │
│       "related_id": "ASSET_database_servers",                   │
│       "related_type": "ASSET",                                  │
│       "relationship_type": "APPLIES_TO",                        │
│       "direction": "outgoing"                                   │
│     },                                                           │
│     {                                                            │
│       "related_id": "REQUIREMENT_REQ-123",                      │
│       "related_type": "REQUIREMENT",                            │
│       "relationship_type": "IMPLEMENTS",                        │
│       "direction": "outgoing"                                   │
│     },                                                           │
│     ... 9 more entities                                         │
│   ]                                                              │
│ }                                                                │
└─────────────────────────────────────────────────────────────────┘
│
▼
┌═════════════════════════════════════════════════════════════════┐
║ 🧠 LLM CALL #3: ASSESS & CONTINUE PLANNING                     ║
║ ─────────────────────────────────────────────────────────────── ║
║ File: llm_adapter.py, Line: 149                                 ║
║ Code: response = self._llm.invoke(prompt)                       ║
║                                                                  ║
║ LLM Receives:                                                    ║
║ - Full conversation history                                      ║
║ - List of 12 connected entities                                 ║
║                                                                  ║
║ LLM Thinks:                                                      ║
║ "I found 12 directly connected entities, but for a complete     ║
║  impact analysis, I need to check for downstream dependencies.  ║
║  Some of these entities might have their own dependencies that  ║
║  would also be affected. Let me use traverse_graph for a        ║
║  deeper analysis with depth=2 to capture cascading impacts."    ║
║                                                                  ║
║ LLM Outputs:                                                     ║
║ {                                                                ║
║   "action": "traverse_graph",                                   ║
║   "action_input": {                                             ║
║     "start_entity_id": "CONTROL_AC-2",                          ║
║     "max_depth": 2                                              ║
║   }                                                              ║
║ }                                                                ║
╚═════════════════════════════════════════════════════════════════╝
│
▼
┌─────────────────────────────────────────────────────────────────┐
│ 🔧 TOOL EXECUTION #3                                            │
│ ─────────────────────────────────────────────────────────────── │
│ File: agent_tools.py                                            │
│ Tool: traverse_graph("CONTROL_AC-2", max_depth=2)              │
│                                                                  │
│ Executes:                                                        │
│ - BFS traversal from AC-2                                       │
│ - Depth 1: 12 entities (direct connections)                     │
│ - Depth 2: 23 additional entities (downstream dependencies)     │
│                                                                  │
│ Returns:                                                         │
│ {                                                                │
│   "start_entity": "CONTROL_AC-2",                               │
│   "max_depth": 2,                                               │
│   "entities_discovered": 35,                                    │
│   "entities": [                                                 │
│     { depth: 0, id: "CONTROL_AC-2", ... },                      │
│     { depth: 1, id: "RISK_R-001", type: "RISK", ... },         │
│     { depth: 1, id: "ASSET_database_servers", ... },           │
│     { depth: 2, id: "POLICY_POL-005", ... },                   │
│     { depth: 2, id: "STANDARD_ISO_27001", ... },               │
│     ... 30 more entities with full dependency tree             │
│   ]                                                              │
│ }                                                                │
└─────────────────────────────────────────────────────────────────┘
│
▼
┌═════════════════════════════════════════════════════════════════┐
║ 🧠 LLM CALL #4: FINAL SYNTHESIS                                ║
║ ─────────────────────────────────────────────────────────────── ║
║ File: llm_adapter.py, Line: 149                                 ║
║ Code: response = self._llm.invoke(prompt)                       ║
║                                                                  ║
║ LLM Receives:                                                    ║
║ - Complete conversation history                                 ║
║ - AC-2 entity details                                           ║
║ - 12 direct relationships                                       ║
║ - 35 total entities in dependency tree                          ║
║ - Depth-2 traversal results                                     ║
║                                                                  ║
║ LLM Thinks:                                                      ║
║ "Perfect! I now have comprehensive information:                 ║
║  - What AC-2 is and does                                        ║
║  - What it directly connects to (depth 1)                       ║
║  - What would be cascading impacted (depth 2)                   ║
║                                                                  ║
║  I can now synthesize a complete impact analysis report."       ║
║                                                                  ║
║ LLM Outputs:                                                     ║
║ [FINAL COMPREHENSIVE ANSWER - FULL TEXT RESPONSE]               ║
║                                                                  ║
║ "Removing control AC-2 (Account Management) would have          ║
║  significant impacts across multiple layers:                    ║
║                                                                  ║
║  IMMEDIATE IMPACTS:                                              ║
║  1. Risk R-001 (Unauthorized Access) - HIGH severity            ║
║     - Currently mitigated by AC-2                               ║
║     - Would become uncontrolled risk                            ║
║                                                                  ║
║  2. Database Servers (ASSET)                                     ║
║     - Would lose primary access control mechanism               ║
║     - 15 production databases affected                          ║
║                                                                  ║
║  3. Requirement REQ-123 - Compliance Mandate                     ║
║     - Would no longer be satisfied                              ║
║     - Creates regulatory gap                                    ║
║                                                                  ║
║  DOWNSTREAM IMPACTS:                                             ║
║  4. Policy POL-005 (Access Management Policy)                   ║
║     - References AC-2 as implementation method                  ║
║     - Policy would have no enforcement mechanism                ║
║                                                                  ║
║  5. ISO 27001 Certification (STANDARD)                           ║
║     - Control A.9.2.1 requirement would be unmet                ║
║     - Could affect certification status                         ║
║                                                                  ║
║  [... detailed analysis continues ...]                          ║
║                                                                  ║
║  TOTAL AFFECTED ENTITIES: 35                                     ║
║  - 8 High-severity risks                                        ║
║  - 15 Critical assets                                           ║
║  - 7 Compliance requirements                                    ║
║  - 5 Related policies                                           ║
║                                                                  ║
║  RECOMMENDATION: Do not remove AC-2 without establishing        ║
║  compensating controls for all identified impacts."             ║
╚═════════════════════════════════════════════════════════════════╝
│
▼
┌─────────────────────────────────────────────────────────────────┐
│ RESPONSE RETURNED TO USER                                       │
│ ─────────────────────────────────────────────────────────────── │
│ File: react_agent.py - Extracts final response                 │
│ File: app.py - Displays to user with "🤖 Agent Mode" badge     │
│                                                                  │
│ User sees comprehensive impact analysis with:                   │
│ - Clear categorization of impacts                               │
│ - Evidence from knowledge graph                                 │
│ - Quantified risk assessment                                    │
│ - Actionable recommendations                                    │
│                                                                  │
│ Optional: Reasoning trace shows all 4 LLM calls + 3 tool uses   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔍 Key Code Locations

### Where LLM is Called (The Critical Line)

**File:** `llm_adapter.py`  
**Line:** 149

```python
response = self._llm.invoke(prompt)  # ← YOUR GOLDMAN SACHS LLM IS CALLED HERE
```

**This single line is executed 4-10+ times during agent execution!**

### Where Agent Gets the LLM

**File:** `react_agent.py`  
**Lines:** 51-55

```python
# Agent is created WITH the LLM
self.agent = create_react_agent(
    model=llm_adapter,  # ← This wraps your GS LLM
    tools=self.tools,   # ← 9 specialized tools
    state_modifier=self.system_prompt
)
```

### Where Agent Execution Starts

**File:** `react_agent.py`  
**Line:** 84

```python
result = self.agent.invoke(
    {"messages": messages},
    config={"recursion_limit": self.max_iterations}
)
```

**This line triggers the entire iterative LLM → Tool → LLM → Tool loop!**

---

## 📊 Comparison: Simple vs Agent Flow

### Simple Flow (1 LLM Call)
```
User Query
    ↓
Build Enhanced Prompt (with KG context)
    ↓
🧠 LLM.invoke(prompt)  ← 1 CALL
    ↓
Response
```

**Total LLM Calls:** 1  
**Processing Time:** 2-3 seconds  
**Best For:** Direct questions with straightforward answers

### Agent Flow (4-10+ LLM Calls)
```
User Query
    ↓
🧠 LLM: "What should I do?" ← CALL #1
    ↓
🔧 Tool Execution #1
    ↓
🧠 LLM: "What next?" ← CALL #2
    ↓
🔧 Tool Execution #2
    ↓
🧠 LLM: "Continue?" ← CALL #3
    ↓
🔧 Tool Execution #3
    ↓
🧠 LLM: "Final answer" ← CALL #4
    ↓
Response
```

**Total LLM Calls:** 4-10+  
**Processing Time:** 5-15 seconds  
**Best For:** Complex multi-step reasoning, impact analysis, gap detection

---

## 💡 The Big Insight

**The agent is NOT a replacement for the LLM.**  
**The agent is the LLM used in a smarter, iterative way!**

### Think of it this way:

**Simple Mode:**  
You give the LLM a huge textbook and ask, "Find information about topic X."  
The LLM reads everything once and answers.

**Agent Mode:**  
You give the LLM tools and say, "Use these tools to thoroughly research topic X."  
The LLM:
1. Uses a tool to search for relevant information
2. Reads the results
3. Decides what to look for next
4. Uses another tool
5. Combines all findings
6. Provides a comprehensive answer

**Same LLM. Just used iteratively with tools instead of all-at-once.**

---

## 🎯 Summary

| Aspect | Simple Flow | Agent Flow |
|--------|-------------|------------|
| **LLM Used** | ✅ Yes (1 call) | ✅ Yes (4-10+ calls) |
| **Tools Used** | ❌ No | ✅ Yes (9 tools) |
| **Iterations** | 1 | 4-10+ |
| **Time** | 2-3 sec | 5-15 sec |
| **Best For** | Simple queries | Complex analysis |
| **Thoroughness** | Good | Excellent |
| **Self-Correction** | ❌ No | ✅ Yes |

---

## 📚 Related Documentation

- **Quick Start:** `AGENT_QUICK_START.md`
- **Implementation Details:** `AGENT_IMPLEMENTATION_SUMMARY.md`
- **Full Guide:** `README.md`
- **Code Reference:** See files mentioned in flow diagram

---

**Remember:** The agent makes your LLM smarter by giving it tools and letting it think step-by-step, not by replacing it!

