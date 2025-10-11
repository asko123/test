# Knowledge Graph Implementation Guide

## Overview

This document describes the Knowledge Graph (KG) enhancement added to the Document Chat Bot system. The KG improves response quality by automatically extracting entities and relationships from documents, providing better context and linkage for the LLM.

## Architecture

### Components

1. **knowledge_graph.py** - Core KG module
   - Entity extraction from text and structured data
   - Relationship detection based on proximity and patterns
   - Graph storage using NetworkX
   - Query and retrieval methods

2. **kg_retriever.py** - Enhanced retrieval system
   - Query analysis and intent detection
   - Context-aware prompt building
   - KG-enhanced document retrieval
   - Statistics and visualization

3. **app.py** - Updated Streamlit application
   - Integration of KG processing
   - UI for enabling/disabling KG
   - Display of KG statistics

## Key Features

### Entity Types

The system automatically extracts the following entity types:

- **CONTROL**: Security controls (e.g., AC-2, ISO-27001-A.9.2.1)
- **RISK**: Risk identifiers and severity levels
- **ASSET**: IT assets (servers, databases, applications, etc.)
- **REQUIREMENT**: Compliance requirements and mandates
- **POLICY**: Security and organizational policies
- **PERSON**: Responsible parties, owners, managers
- **STANDARD**: Compliance frameworks (NIST, ISO, SOC, PCI, etc.)

### Relationship Types

The KG detects the following relationship types:

- **IMPLEMENTS**: Controls implementing requirements
- **MITIGATES**: Controls mitigating risks
- **REQUIRES**: Dependencies between entities
- **OWNS**: Ownership relationships
- **APPLIES_TO**: Applicability relationships
- **RELATES_TO**: General relationships

### Entity Extraction Methods

#### Text-based Extraction
Uses regex patterns to identify entities in unstructured text:
```python
ENTITY_PATTERNS = {
    'CONTROL': [
        r'control[_\s]+(?:id|ID|number|#)?[:\s]*([A-Z0-9\-\.]+)',
        r'(?:AC|AU|CM|IA|IR|MA|PE|PS|RA|SA|SC|SI|SR)-\d{1,3}(?:\(\d+\))?',
    ],
    'RISK': [
        r'risk[_\s]+(?:id|ID|number|#)?[:\s]*([A-Z0-9\-\.]+)',
        r'(?:high|medium|low|critical)\s+risk',
    ],
    # ... more patterns
}
```

#### JSON-based Extraction
Extracts entities from structured JSON/JSONL data by analyzing keys and values:
- Identifies entity types based on field names
- Tracks JSON paths for source tracing
- Handles nested structures recursively

### Relationship Detection

The system detects relationships through:

1. **Proximity Analysis**: Entities close together in text (within 200 characters) are likely related
2. **Pattern Matching**: Looks for relationship indicators like "implements", "mitigates", "requires"
3. **Confidence Scoring**: Assigns confidence scores based on evidence strength

### Query Enhancement

When a user asks a question, the KG Retriever:

1. **Analyzes the Query**
   - Detects intent (list, explain, relationship, compliance, impact, etc.)
   - Identifies relevant entity types
   
2. **Retrieves Relevant Context**
   - Finds entities mentioned in the query
   - Gets related entities up to N hops away
   - Ranks by relevance score
   
3. **Builds Enhanced Prompt**
   - Combines KG context with original document content
   - Adds intent-specific instructions
   - Provides structured entity and relationship information

## Usage

### Enabling Knowledge Graph

In the Streamlit UI:
1. Check "Enable Knowledge Graph Enhancement" in the sidebar
2. Upload your documents
3. Click "Process Documents"
4. The system will build the KG automatically

### Viewing KG Statistics

After processing documents, expand "View KG Statistics" in the sidebar to see:
- Total entities by type
- Total relationships by type
- Graph density and connectivity metrics

### Query Examples

#### Without KG:
```
User: "What controls address database security?"
Response: Basic text search through documents
```

#### With KG:
```
User: "What controls address database security?"
Response: 
- Identifies all CONTROL entities
- Finds relationships to ASSET entities (databases)
- Shows which controls APPLY_TO or MITIGATE database risks
- Provides comprehensive, connected information
```

## Benefits

### 1. Better Context Understanding
- Entities are recognized and linked across documents
- Relationships provide semantic connections
- Context is preserved even when entities are far apart in text

### 2. Improved Response Quality
- More accurate answers with better entity recognition
- Comprehensive coverage through relationship traversal
- Precise source attribution

### 3. Enhanced Analysis
- Can answer relationship questions ("How are X and Y connected?")
- Better handling of multi-entity queries
- Impact analysis through relationship graphs

### 4. Structured Information
- Entities organized by type
- Relationships categorized
- Metadata tracked for each entity

## Implementation Details

### Graph Storage

Uses NetworkX MultiDiGraph:
- Nodes: Entities with attributes (type, value, context, source)
- Edges: Relationships with attributes (type, evidence, confidence)
- Allows multiple relationships between same entities

### Performance Considerations

1. **Entity Extraction**: O(n) where n = document size
2. **Relationship Detection**: O(m²) where m = entities per document
3. **Query Time**: O(k + d*e) where k = matching entities, d = depth, e = edges per node

### Memory Usage

For typical documents:
- 1000 entities: ~5-10MB
- 5000 relationships: ~10-20MB
- NetworkX graph overhead: ~5MB

## Advanced Features

### Custom Entity Patterns

Extend entity patterns in `knowledge_graph.py`:
```python
ENTITY_PATTERNS['CUSTOM_TYPE'] = [
    r'your_pattern_here',
]
```

### Relationship Pattern Tuning

Adjust relationship detection in `detect_relationships()`:
- Modify proximity threshold (default: 200 chars)
- Add new relationship patterns
- Adjust confidence scoring

### Query Intent Detection

Add new query intents in `kg_retriever.py`:
```python
intent_patterns['new_intent'] = [r'pattern1', r'pattern2']
```

## Testing

### Unit Tests

Test entity extraction:
```python
from knowledge_graph import KnowledgeGraph

kg = KnowledgeGraph()
entities = kg.extract_entities_from_text(
    "Control AC-2 implements requirement REQ-001",
    "test_doc.txt"
)
assert len(entities) >= 2
```

### Integration Tests

Test end-to-end flow:
```python
from kg_retriever import KGRetriever

retriever = KGRetriever()
documents = [{'name': 'test.txt', 'content': '...'}]
retriever.build_knowledge_graph(documents)
context = retriever.get_enhanced_context("What controls exist?", "...")
assert 'KNOWLEDGE GRAPH CONTEXT' in context
```

## Troubleshooting

### Issue: No entities extracted
**Solution**: Check if documents contain recognizable patterns. Add custom patterns if needed.

### Issue: Too many false positives
**Solution**: Make patterns more specific or increase context window for validation.

### Issue: Missing relationships
**Solution**: Adjust proximity threshold or add more relationship patterns.

### Issue: Slow processing
**Solution**: Reduce relationship detection range or limit entity extraction patterns.

## Future Enhancements

1. **Machine Learning**: Use NER models for better entity extraction
2. **Graph Visualization**: Add interactive graph visualization in UI
3. **Advanced Queries**: Support graph query languages (Cypher-like)
4. **Persistent Storage**: Save KG to Neo4j or other graph databases
5. **Entity Disambiguation**: Handle entities with similar names
6. **Temporal Relationships**: Track changes over time
7. **Confidence Propagation**: Improve confidence scoring across relationship chains

## API Reference

### KnowledgeGraph Class

#### Methods

- `extract_entities_from_text(text, doc_name)` - Extract entities from text
- `extract_entities_from_json(json_data, doc_name)` - Extract from JSON
- `detect_relationships(entities, text)` - Find relationships
- `add_entity(entity)` - Add entity to graph
- `add_relationship(source, target, type, metadata)` - Add relationship
- `query_entities(entity_type, value_pattern)` - Search entities
- `get_related_entities(entity_id, max_depth)` - Get related entities
- `get_context_for_query(query, top_k)` - Get relevant context
- `get_statistics()` - Get graph statistics

### KGRetriever Class

#### Methods

- `build_knowledge_graph(documents)` - Build KG from documents
- `get_enhanced_context(query, original_content)` - Get enhanced context
- `analyze_query(query)` - Analyze query intent
- `build_contextual_prompt(query, original_content)` - Build enhanced prompt
- `get_statistics()` - Get KG statistics
- `search_entities(entity_type, value_pattern)` - Search entities
- `export_graph_summary()` - Export summary for display

## References

- NetworkX Documentation: https://networkx.org/
- Entity Recognition Patterns: Based on NIST SP 800-53, ISO 27001
- Graph Theory: Relationship detection using BFS traversal

## License

Same as main project license.

## Support

For questions or issues, refer to the main README.md or contact the development team.

