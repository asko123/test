"""
Test script for Knowledge Graph functionality
Run this to validate the KG implementation
"""

import sys
from knowledge_graph import KnowledgeGraph
from kg_retriever import KGRetriever


def test_entity_extraction():
    """Test entity extraction from text."""
    print("\n" + "="*60)
    print("TEST 1: Entity Extraction from Text")
    print("="*60)
    
    kg = KnowledgeGraph()
    
    test_text = """
    Security Control AC-2 (Account Management) is designed to mitigate 
    high risk R-001. The control requires proper authentication and applies 
    to database servers and application servers. This control implements 
    NIST SP 800-53 requirement and is owned by Security Manager John Smith.
    The asset type includes critical databases and must comply with 
    ISO 27001 standard.
    """
    
    entities = kg.extract_entities_from_text(test_text, "test_doc.txt")
    
    print(f"✓ Extracted {len(entities)} entities:")
    entity_types = {}
    for entity in entities:
        entity_type = entity['type']
        entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
        print(f"  - {entity['type']}: {entity['value']}")
    
    print(f"\n✓ Entity type summary: {entity_types}")
    
    # Assertions
    assert len(entities) > 0, "Should extract at least one entity"
    assert any(e['type'] == 'CONTROL' for e in entities), "Should extract CONTROL entities"
    assert any(e['type'] == 'RISK' for e in entities), "Should extract RISK entities"
    
    print("\n[PASS] Entity extraction test PASSED")
    return True


def test_json_extraction():
    """Test entity extraction from JSON."""
    print("\n" + "="*60)
    print("TEST 2: Entity Extraction from JSON")
    print("="*60)
    
    kg = KnowledgeGraph()
    
    test_json = {
        "controls": [
            {
                "control_id": "AC-3",
                "control_name": "Access Enforcement",
                "risk_level": "medium",
                "asset_type": "application",
                "responsible": "IT Manager"
            },
            {
                "control_id": "AU-2",
                "control_name": "Audit Events",
                "risk_level": "low",
                "asset_type": "server"
            }
        ]
    }
    
    entities = kg.extract_entities_from_json(test_json, "test.json")
    
    print(f"✓ Extracted {len(entities)} entities from JSON:")
    for entity in entities[:10]:  # Show first 10
        print(f"  - {entity['type']}: {entity['value']} (path: {entity.get('json_path', 'N/A')})")
    
    # Assertions
    assert len(entities) > 0, "Should extract entities from JSON"
    assert any('json_path' in e for e in entities), "Should track JSON paths"
    
    print("\n[PASS] JSON extraction test PASSED")
    return True


def test_relationship_detection():
    """Test relationship detection."""
    print("\n" + "="*60)
    print("TEST 3: Relationship Detection")
    print("="*60)
    
    kg = KnowledgeGraph()
    
    test_text = """
    Control AC-2 mitigates Risk R-001. The control implements Requirement 
    REQ-123 and applies to Asset DB-Server-01. This control is owned by 
    Security Team and relates to ISO 27001 standard.
    """
    
    entities = kg.extract_entities_from_text(test_text, "test.txt")
    relationships = kg.detect_relationships(entities, test_text)
    
    print(f"✓ Detected {len(relationships)} relationships:")
    for src, tgt, rel_type, meta in relationships[:10]:  # Show first 10
        print(f"  - {rel_type}: {src} -> {tgt}")
        if 'evidence' in meta:
            print(f"    Evidence: {meta['evidence'][:50]}...")
    
    # Assertions
    assert len(relationships) > 0, "Should detect relationships"
    assert any(rel[2] != 'RELATES_TO' for rel in relationships), "Should detect specific relationship types"
    
    print("\n[PASS] Relationship detection test PASSED")
    return True


def test_graph_building():
    """Test knowledge graph building."""
    print("\n" + "="*60)
    print("TEST 4: Knowledge Graph Building")
    print("="*60)
    
    kg = KnowledgeGraph()
    
    documents = [
        {
            'name': 'security_controls.txt',
            'content': """
                Control AC-2 implements user account management to mitigate 
                unauthorized access risk R-005. This applies to all database 
                servers and requires approval from Security Manager.
            """
        },
        {
            'name': 'risk_assessment.txt',
            'content': """
                High Risk R-005: Unauthorized access to sensitive data.
                Mitigation: Implement Control AC-2 and Control AC-3.
                Affected Assets: Database servers, application servers.
                Standard: NIST SP 800-53, ISO 27001.
            """
        }
    ]
    
    kg.build_from_documents(documents)
    stats = kg.get_statistics()
    
    print(f"✓ Graph statistics:")
    print(f"  - Documents: {stats['document_count']}")
    print(f"  - Entities: {stats['entity_count']}")
    print(f"  - Relationships: {stats['relationship_count']}")
    print(f"  - Entity types: {stats['entity_types']}")
    print(f"  - Graph density: {stats['graph_density']:.4f}")
    
    # Assertions
    assert stats['entity_count'] > 0, "Should have entities"
    assert stats['relationship_count'] > 0, "Should have relationships"
    assert len(stats['entity_types']) > 0, "Should have entity types"
    
    print("\n[PASS] Graph building test PASSED")
    return True


def test_query_context():
    """Test query context retrieval."""
    print("\n" + "="*60)
    print("TEST 5: Query Context Retrieval")
    print("="*60)
    
    kg = KnowledgeGraph()
    
    documents = [
        {
            'name': 'controls.txt',
            'content': """
                Control AC-2 (Account Management) addresses Risk R-001.
                Control AU-2 (Audit Events) monitors access to servers.
                Asset Type: Database servers, application servers.
                Standard: NIST SP 800-53.
            """
        }
    ]
    
    kg.build_from_documents(documents)
    
    # Test query
    query = "What controls address account management?"
    context = kg.get_context_for_query(query, top_k=5)
    
    print(f"✓ Query: '{query}'")
    print(f"✓ Found {context['total_entities']} relevant entities:")
    for entity in context['entities'][:5]:
        print(f"  - {entity['entity_type']}: {entity['value']} (relevance: {entity['relevance_score']:.2f})")
    
    print(f"\n✓ Found {context['total_relationships']} related entities")
    
    # Assertions
    assert context['total_entities'] > 0, "Should find relevant entities"
    assert 'entities' in context, "Should return entities list"
    assert 'relationships' in context, "Should return relationships list"
    
    print("\n[PASS] Query context test PASSED")
    return True


def test_kg_retriever():
    """Test KG Retriever."""
    print("\n" + "="*60)
    print("TEST 6: KG Retriever Integration")
    print("="*60)
    
    retriever = KGRetriever()
    
    documents = [
        {
            'name': 'security_policy.txt',
            'content': """
                Security Policy POL-001 mandates Control AC-2 for account management.
                This control mitigates Risk R-003 (Unauthorized Access).
                Applicable to: Database servers, web servers.
                Compliance: ISO 27001, NIST SP 800-53.
                Owner: Security Manager Jane Doe.
            """
        }
    ]
    
    retriever.build_knowledge_graph(documents)
    stats = retriever.get_statistics()
    
    print(f"✓ KG Retriever statistics:")
    print(f"  - Entities: {stats['entity_count']}")
    print(f"  - Relationships: {stats['relationship_count']}")
    
    # Test query analysis
    query = "What controls mitigate unauthorized access?"
    analysis = retriever.analyze_query(query)
    
    print(f"\n✓ Query analysis for: '{query}'")
    print(f"  - Intent: {analysis['intent']}")
    print(f"  - Relevant entity types: {analysis['relevant_entity_types']}")
    
    # Test enhanced context
    enhanced = retriever.get_enhanced_context(query, documents[0]['content'], top_k=5)
    
    print(f"\n✓ Enhanced context generated ({len(enhanced)} chars)")
    print(f"  Contains KG context: {'KNOWLEDGE GRAPH CONTEXT' in enhanced}")
    print(f"  Contains original content: {'ORIGINAL DOCUMENT CONTENT' in enhanced}")
    
    # Assertions
    assert stats['entity_count'] > 0, "Should have entities"
    assert analysis['intent'] is not None, "Should detect intent"
    assert 'KNOWLEDGE GRAPH CONTEXT' in enhanced, "Should include KG context"
    
    print("\n[PASS] KG Retriever test PASSED")
    return True


def test_contextual_prompt():
    """Test contextual prompt building."""
    print("\n" + "="*60)
    print("TEST 7: Contextual Prompt Building")
    print("="*60)
    
    retriever = KGRetriever()
    
    documents = [
        {
            'name': 'test.txt',
            'content': "Control AC-2 mitigates Risk R-001 affecting database servers."
        }
    ]
    
    retriever.build_knowledge_graph(documents)
    
    query = "What are the security controls?"
    prompt = retriever.build_contextual_prompt(query, documents[0]['content'])
    
    print(f"✓ Generated contextual prompt ({len(prompt)} chars)")
    print(f"  Contains query analysis: {'QUERY ANALYSIS' in prompt}")
    print(f"  Contains KG context: {'KNOWLEDGE GRAPH CONTEXT' in prompt}")
    print(f"  Contains instructions: {'RESPONSE INSTRUCTIONS' in prompt}")
    print(f"  Contains user question: {query in prompt}")
    
    # Show sample of prompt
    print(f"\n✓ Prompt preview (first 500 chars):")
    print(prompt[:500] + "...")
    
    # Assertions
    assert 'QUERY ANALYSIS' in prompt, "Should include query analysis"
    assert 'KNOWLEDGE GRAPH CONTEXT' in prompt, "Should include KG context"
    assert query in prompt, "Should include user question"
    
    print("\n[PASS] Contextual prompt test PASSED")
    return True


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("KNOWLEDGE GRAPH TEST SUITE")
    print("="*60)
    
    tests = [
        ("Entity Extraction", test_entity_extraction),
        ("JSON Extraction", test_json_extraction),
        ("Relationship Detection", test_relationship_detection),
        ("Graph Building", test_graph_building),
        ("Query Context", test_query_context),
        ("KG Retriever", test_kg_retriever),
        ("Contextual Prompt", test_contextual_prompt),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n[FAIL] {test_name} test FAILED with error: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "[PASS] PASSED" if success else "[FAIL] FAILED"
        print(f"{status} - {test_name}")
    
    print("\n" + "="*60)
    print(f"Results: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        print("\n[SUCCESS] All tests passed! Knowledge Graph is working correctly.")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())

