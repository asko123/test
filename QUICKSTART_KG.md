# Knowledge Graph Quick Start Guide

##  Get Started in 3 Minutes

### Step 1: Install Dependencies
```bash
cd /Users/Tawfiq/Desktop/test
pip install networkx>=3.1 matplotlib>=3.7.0
```

### Step 2: Run the Application
```bash
streamlit run app.py
```

### Step 3: Enable Knowledge Graph
1. In the sidebar, check  **"Enable Knowledge Graph Enhancement"**
2. Upload your documents (PDF, JSON, JSONL, or TXT)
3. Click **"Process Documents"**
4. Wait for KG to build (you'll see: "Building Knowledge Graph...")

### Step 4: Ask Questions!

Try these example queries:

#### List Queries
- "What controls are in the document?"
- "List all high-severity risks"
- "Show me all assets mentioned"

#### Relationship Queries
- "How are control AC-2 and database security related?"
- "What controls mitigate unauthorized access risks?"
- "Which requirements does control AC-2 implement?"

#### Compliance Queries
- "Which controls satisfy NIST SP 800-53?"
- "What are the ISO 27001 requirements?"
- "Show compliance mapping for control AC-2"

#### Impact Analysis
- "What would be affected if we remove control AC-2?"
- "What assets are protected by access controls?"
- "Which policies apply to database servers?"

##  View Your Knowledge Graph

After processing documents, expand **" View KG Statistics"** in the sidebar to see:
- Total entities by type (Controls, Risks, Assets, etc.)
- Total relationships detected
- Graph connectivity metrics

##  Verify Installation

Run the test suite:
```bash
python test_kg.py
```

Expected output:
```
 All tests passed! Knowledge Graph is working correctly.
Results: 7/7 tests passed
```

##  What Makes KG Better?

### Without KG:
```
Query: "What controls protect databases?"
Response: [searches for "control" and "database" in text]
```

### With KG:
```
Query: "What controls protect databases?"
Response: 
 Identifies all CONTROL entities
 Finds ASSET entities (databases)
 Shows relationships: CONTROL --[APPLIES_TO]--> ASSET
 Includes connected RISK and REQUIREMENT entities
 Provides comprehensive, connected answer
```

##  Toggle KG On/Off

You can toggle KG anytime:
- **ON**: Better context, entity tracking, relationship awareness
- **OFF**: Traditional text-based search (faster but less accurate)

Compare responses with KG on vs. off to see the difference!

##  Learn More

- **Detailed Guide**: `KG_IMPLEMENTATION_GUIDE.md`
- **Upgrade Summary**: `KG_UPGRADE_SUMMARY.md`
- **Full README**: `README.md`

##  Tips for Best Results

1. **Enable KG for complex documents**: Security policies, compliance frameworks, risk assessments
2. **Use specific queries**: "What controls..." instead of just "controls"
3. **Ask relationship questions**: "How is X related to Y?"
4. **Request structured answers**: "List all..." or "Show me..."
5. **Check KG stats**: Ensure entities were extracted from your documents

## 🆘 Troubleshooting

**No entities extracted?**
- Check if your documents use standard terminology (controls, risks, assets)
- Add custom patterns in `knowledge_graph.py` for domain-specific terms

**Slow processing?**
- Normal for first-time processing
- Subsequent queries are fast (KG is already built)

**Want to customize?**
- Edit entity patterns in `knowledge_graph.py`
- Adjust relationship detection in `detect_relationships()`
- Modify query intents in `kg_retriever.py`

##  You're Ready!

Start chatting with your documents and experience the power of Knowledge Graph-enhanced responses!

