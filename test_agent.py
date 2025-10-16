"""
Test Suite for LangGraph ReAct Agent Integration
Tests for agent, tools, routing, and end-to-end functionality
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json

# Import modules to test
from query_router import QueryRouter, route_query
from agent_state import AgentState, AgentMemory
from knowledge_graph import KnowledgeGraph
from kg_retriever import KGRetriever


class TestQueryRouter(unittest.TestCase):
    """Test the query routing logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.router = QueryRouter(complexity_threshold=60)
    
    def test_simple_query_detection(self):
        """Test that simple queries are routed to simple flow."""
        simple_queries = [
            "What is AC-2?",
            "List all controls",
            "Explain control AC-2",
        ]
        
        for query in simple_queries:
            use_agent, analysis = self.router.should_use_agent(query)
            self.assertFalse(use_agent, f"Simple query should not use agent: {query}")
    
    def test_complex_query_detection(self):
        """Test that complex queries are routed to agent."""
        complex_queries = [
            "How does AC-2 relate to database security compliance across ISO 27001 and NIST 800-53?",
            "What would be affected if we remove control AC-2?",
            "Which high-severity risks don't have mitigation controls?",
            "Compare controls for ISO 27001 versus NIST",
        ]
        
        for query in complex_queries:
            use_agent, analysis = self.router.should_use_agent(query)
            self.assertTrue(use_agent, f"Complex query should use agent: {query}")
    
    def test_complexity_scoring(self):
        """Test complexity scoring algorithm."""
        # Very simple query
        score1 = self.router.calculate_complexity_score("What is AC-2?")
        
        # Complex query
        score2 = self.router.calculate_complexity_score(
            "How does AC-2 relate to database security compliance across multiple frameworks?"
        )
        
        self.assertLess(score1, score2, "Complex query should have higher score")
        self.assertGreater(score2, 50, "Complex query should exceed threshold")
    
    def test_query_type_detection(self):
        """Test query type detection."""
        test_cases = [
            ("How does X relate to Y?", "multi_hop"),
            ("What would be affected?", "impact_analysis"),
            ("Which controls are missing?", "gap_analysis"),
            ("What is AC-2?", "explain"),
        ]
        
        for query, expected_type in test_cases:
            detected_type = self.router.detect_query_type(query)
            self.assertEqual(detected_type, expected_type)


class TestAgentState(unittest.TestCase):
    """Test agent state management."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.state = AgentState()
    
    def test_entity_tracking(self):
        """Test entity discovery tracking."""
        entity_data = {
            'type': 'CONTROL',
            'value': 'AC-2',
            'source': 'test.pdf'
        }
        
        self.state.add_discovered_entity('CONTROL_AC-2', entity_data)
        
        self.assertIn('CONTROL_AC-2', self.state.discovered_entities)
        self.assertEqual(self.state.entity_access_count['CONTROL_AC-2'], 1)
    
    def test_relationship_tracking(self):
        """Test relationship tracking."""
        self.state.add_relationship('CONTROL_AC-2', 'RISK_R-001', 'MITIGATES')
        
        self.assertEqual(len(self.state.explored_relationships), 1)
        self.assertEqual(self.state.explored_relationships[0][2], 'MITIGATES')
    
    def test_tool_call_recording(self):
        """Test tool call recording."""
        self.state.record_tool_call(
            'search_entities',
            {'entity_type': 'CONTROL'},
            '{"count": 5}',
            True
        )
        
        self.assertEqual(len(self.state.tool_calls), 1)
        self.assertEqual(self.state.tool_usage_count['search_entities'], 1)
    
    def test_conversation_history(self):
        """Test conversation tracking."""
        self.state.add_to_conversation(
            "What is AC-2?",
            "AC-2 is a control for account management.",
            {'complexity': 'low'}
        )
        
        self.assertEqual(len(self.state.conversation_history), 1)
        self.assertEqual(self.state.conversation_history[0]['query'], "What is AC-2?")
    
    def test_statistics_generation(self):
        """Test statistics generation."""
        # Add some data
        self.state.add_discovered_entity('CONTROL_AC-2', {'type': 'CONTROL'})
        self.state.add_relationship('CONTROL_AC-2', 'RISK_R-001', 'MITIGATES')
        self.state.record_tool_call('search_entities', {}, '{}', True)
        
        stats = self.state.get_statistics()
        
        self.assertEqual(stats['entities_discovered'], 1)
        self.assertEqual(stats['relationships_explored'], 1)
        self.assertEqual(stats['tool_calls_made'], 1)


class TestAgentMemory(unittest.TestCase):
    """Test agent memory management."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.memory = AgentMemory()
    
    def test_session_creation(self):
        """Test creating new sessions."""
        session1 = self.memory.create_session("test_session_1")
        
        self.assertIsNotNone(session1)
        self.assertEqual(session1.session_id, "test_session_1")
        self.assertIn("test_session_1", self.memory.sessions)
    
    def test_session_retrieval(self):
        """Test retrieving sessions."""
        session1 = self.memory.create_session("test_session_1")
        retrieved = self.memory.get_session("test_session_1")
        
        self.assertEqual(session1, retrieved)
    
    def test_current_session_management(self):
        """Test current session tracking."""
        session1 = self.memory.create_session("test_session_1")
        
        self.assertEqual(self.memory.current_session_id, "test_session_1")
        
        current = self.memory.get_current_session()
        self.assertEqual(current, session1)


class TestKnowledgeGraphWithAgent(unittest.TestCase):
    """Test Knowledge Graph functionality for agent use."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.kg = KnowledgeGraph()
        
        # Add sample data
        self.sample_documents = [
            {
                'name': 'test_doc.txt',
                'content': 'Control AC-2 mitigates unauthorized access risk R-001 affecting database servers.'
            }
        ]
        
        self.kg.build_from_documents(self.sample_documents)
    
    def test_entity_extraction(self):
        """Test that entities are extracted."""
        stats = self.kg.get_statistics()
        self.assertGreater(stats['entity_count'], 0, "Should extract entities")
    
    def test_relationship_detection(self):
        """Test that relationships are detected."""
        stats = self.kg.get_statistics()
        self.assertGreater(stats['relationship_count'], 0, "Should detect relationships")
    
    def test_entity_query(self):
        """Test querying entities."""
        controls = self.kg.query_entities(entity_type='CONTROL')
        self.assertGreater(len(controls), 0, "Should find control entities")
    
    def test_context_for_query(self):
        """Test getting context for a query."""
        context = self.kg.get_context_for_query("What controls protect databases?")
        
        self.assertIn('entities', context)
        self.assertIn('relationships', context)


class TestKGRetriever(unittest.TestCase):
    """Test KG Retriever functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.kg_retriever = KGRetriever()
        
        # Build sample KG
        self.sample_documents = [
            {
                'name': 'test_doc.txt',
                'content': 'Control AC-2 manages user accounts for database servers to mitigate unauthorized access risk.'
            }
        ]
        
        self.kg_retriever.build_knowledge_graph(self.sample_documents)
    
    def test_kg_building(self):
        """Test that KG is built successfully."""
        stats = self.kg_retriever.get_statistics()
        self.assertGreater(stats['entity_count'], 0)
    
    def test_query_analysis(self):
        """Test query analysis."""
        analysis = self.kg_retriever.analyze_query("How does AC-2 relate to database security?")
        
        self.assertIn('intent', analysis)
        self.assertIn('relevant_entity_types', analysis)
    
    def test_contextual_prompt_building(self):
        """Test building contextual prompts."""
        prompt = self.kg_retriever.build_contextual_prompt(
            "What is AC-2?",
            "Sample document content"
        )
        
        self.assertIn("Knowledge Graph", prompt.upper())
        self.assertIn("AC-2", prompt or "")


def run_integration_tests():
    """
    Run integration tests that require full setup.
    These tests are optional and may require actual LLM access.
    """
    print("\n" + "="*50)
    print("INTEGRATION TESTS (Optional - requires full setup)")
    print("="*50)
    
    # Test 1: Full routing flow
    print("\n1. Testing query routing...")
    router = QueryRouter()
    
    test_queries = [
        "What is AC-2?",
        "How does AC-2 relate to ISO 27001 and NIST compliance across all database controls?"
    ]
    
    for query in test_queries:
        use_agent, analysis = router.should_use_agent(query)
        print(f"   Query: {query[:50]}...")
        print(f"   Route: {'Agent' if use_agent else 'Simple'} (score: {analysis['complexity_score']})")
    
    print("\n✓ Integration tests completed!")


def main():
    """Run all tests."""
    print("Starting LangGraph ReAct Agent Test Suite\n")
    
    # Run unit tests
    unittest.main(argv=[''], verbosity=2, exit=False)
    
    # Run integration tests
    try:
        run_integration_tests()
    except Exception as e:
        print(f"\n⚠️  Integration tests skipped: {str(e)}")
    
    print("\n" + "="*50)
    print("Test suite completed!")
    print("="*50)


if __name__ == '__main__':
    main()

