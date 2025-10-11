"""
Knowledge Graph Enhanced Retrieval System
Combines knowledge graph context with document content for improved LLM responses
"""

from typing import Dict, List, Any, Optional
from knowledge_graph import KnowledgeGraph
import re
import json


class KGRetriever:
    """Enhanced retrieval system using Knowledge Graph."""
    
    def __init__(self):
        """Initialize the KG Retriever."""
        self.kg = KnowledgeGraph()
        self.documents = []
        
    def build_knowledge_graph(self, documents: List[Dict[str, Any]]):
        """
        Build knowledge graph from documents.
        
        Args:
            documents: List of document dictionaries with 'name', 'content', and optional 'json_data'
        """
        self.documents = documents
        self.kg.build_from_documents(documents)
        
    def get_enhanced_context(self, query: str, original_content: str, top_k: int = 15) -> str:
        """
        Get enhanced context by combining KG insights with original content.
        
        Args:
            query: User query
            original_content: Original document content
            top_k: Number of top entities to retrieve
            
        Returns:
            Enhanced context string
        """
        # Get KG context for the query
        kg_context = self.kg.get_context_for_query(query, top_k=top_k)
        
        # Format KG context for LLM
        kg_formatted = self.kg.export_for_llm(kg_context)
        
        # Combine with original content
        enhanced_context = f"""{kg_formatted}

=== ORIGINAL DOCUMENT CONTENT ===

{original_content}

"""
        return enhanced_context
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze query to extract intent and relevant entity types.
        
        Args:
            query: User query
            
        Returns:
            Dictionary with query analysis
        """
        query_lower = query.lower()
        
        # Detect query intent
        intent_patterns = {
            'list_controls': [r'list.*control', r'what controls', r'show.*control', r'all controls'],
            'list_risks': [r'list.*risk', r'what risks', r'show.*risk', r'all risks'],
            'explain': [r'what is', r'explain', r'describe', r'tell me about'],
            'relationship': [r'how.*relate', r'connect', r'relationship', r'link', r'associate'],
            'compliance': [r'comply', r'standard', r'requirement', r'mandate'],
            'impact': [r'impact', r'affect', r'consequence', r'result'],
        }
        
        detected_intent = 'general'
        for intent, patterns in intent_patterns.items():
            if any(re.search(pattern, query_lower) for pattern in patterns):
                detected_intent = intent
                break
        
        # Detect relevant entity types
        entity_keywords = {
            'CONTROL': ['control', 'safeguard', 'protection'],
            'RISK': ['risk', 'threat', 'vulnerability', 'danger'],
            'ASSET': ['asset', 'resource', 'system', 'server', 'database'],
            'REQUIREMENT': ['requirement', 'must', 'shall', 'should'],
            'POLICY': ['policy', 'rule', 'guideline'],
            'PERSON': ['owner', 'responsible', 'manager'],
            'STANDARD': ['standard', 'framework', 'nist', 'iso', 'compliance'],
        }
        
        relevant_entities = []
        for entity_type, keywords in entity_keywords.items():
            if any(kw in query_lower for kw in keywords):
                relevant_entities.append(entity_type)
        
        return {
            'intent': detected_intent,
            'relevant_entity_types': relevant_entities,
            'query_length': len(query.split()),
        }
    
    def build_contextual_prompt(self, query: str, original_content: str) -> str:
        """
        Build an enhanced prompt with KG context and query analysis.
        
        Args:
            query: User query
            original_content: Original document content
            
        Returns:
            Enhanced prompt for LLM
        """
        # Analyze the query
        query_analysis = self.analyze_query(query)
        
        # Get enhanced context
        enhanced_context = self.get_enhanced_context(query, original_content)
        
        # Build intent-specific instructions
        intent_instructions = self._get_intent_instructions(query_analysis['intent'])
        
        # Build the prompt
        prompt = f"""You are an advanced cybersecurity and risk analysis assistant with access to a Knowledge Graph of document entities and relationships.

QUERY ANALYSIS:
- Intent: {query_analysis['intent']}
- Relevant Entity Types: {', '.join(query_analysis['relevant_entity_types']) if query_analysis['relevant_entity_types'] else 'All types'}

{enhanced_context}

=== USER QUESTION ===
{query}

=== RESPONSE INSTRUCTIONS ===

{intent_instructions}

General Guidelines:
1. **Leverage the Knowledge Graph**: Use the entity relationships to provide connected, comprehensive answers
2. **Cite Sources Precisely**: Reference specific entities, documents, and relationships from the KG
3. **Show Connections**: When relevant, explain how different entities relate to each other
4. **Structure Your Response**:
   - Start with a direct answer to the question
   - Provide supporting details from the KG and documents
   - Highlight important relationships and dependencies
   - Include relevant entity details (IDs, types, sources)
5. **Format for Readability**:
   - Use bullet points for lists of entities or relationships
   - Use numbered lists for procedures or sequential information
   - Bold important entity names and IDs
   - Include clear paragraph breaks
6. **Be Comprehensive but Concise**: Cover all relevant entities and relationships without overwhelming detail
7. **Handle Missing Information**: If the KG or documents lack certain information, state what is available and what is not

Answer:"""
        
        return prompt
    
    def _get_intent_instructions(self, intent: str) -> str:
        """
        Get specific instructions based on detected query intent.
        
        Args:
            intent: Detected intent
            
        Returns:
            Intent-specific instructions
        """
        instructions = {
            'list_controls': """
For listing controls:
- Provide a comprehensive list with control IDs and names
- Group by type or source if applicable
- Include brief descriptions
- Mention related risks or requirements if available in the KG
""",
            'list_risks': """
For listing risks:
- List all identified risks with IDs and severity levels
- Group by severity (Critical, High, Medium, Low)
- Include related controls that mitigate each risk
- Mention affected assets if available
""",
            'explain': """
For explanations:
- Start with a clear definition or description
- Include all relevant attributes from the KG entity
- Explain relationships to other entities
- Provide context from the source documents
""",
            'relationship': """
For relationship queries:
- Clearly identify the entities involved
- Explain the type and nature of their relationship
- Include the evidence or rationale for the relationship
- Visualize the connection chain if multiple hops are involved
""",
            'compliance': """
For compliance queries:
- Identify the relevant standards and requirements
- List applicable controls and their mappings
- Explain how requirements are satisfied
- Highlight any gaps or missing information
""",
            'impact': """
For impact analysis:
- Identify the source entity (what's causing the impact)
- List all affected entities based on KG relationships
- Explain the nature and severity of the impact
- Suggest mitigation controls if available
""",
            'general': """
For general queries:
- Provide a comprehensive answer using all available information
- Highlight key entities and their relationships
- Structure the response logically
- Include supporting evidence from documents
"""
        }
        
        return instructions.get(intent, instructions['general'])
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the knowledge graph.
        
        Returns:
            Statistics dictionary
        """
        return self.kg.get_statistics()
    
    def search_entities(self, entity_type: str = None, value_pattern: str = None) -> List[Dict[str, Any]]:
        """
        Search for entities in the knowledge graph.
        
        Args:
            entity_type: Filter by entity type
            value_pattern: Pattern to match in entity values
            
        Returns:
            List of matching entities
        """
        return self.kg.query_entities(entity_type=entity_type, value_pattern=value_pattern)
    
    def get_entity_relationships(self, entity_id: str, max_depth: int = 2) -> List[Dict[str, Any]]:
        """
        Get relationships for a specific entity.
        
        Args:
            entity_id: Entity ID
            max_depth: Maximum relationship depth
            
        Returns:
            List of related entities
        """
        return self.kg.get_related_entities(entity_id, max_depth=max_depth)
    
    def export_graph_summary(self) -> str:
        """
        Export a summary of the knowledge graph for display.
        
        Returns:
            Formatted summary string
        """
        stats = self.get_statistics()
        
        summary = f"""
### Knowledge Graph Summary

**Overall Statistics:**
- Total Documents Processed: {stats['document_count']}
- Total Entities Extracted: {stats['entity_count']}
- Total Relationships: {stats['relationship_count']}
- Graph Density: {stats['graph_density']:.4f}
- Connected Components: {stats['connected_components']}

**Entity Types:**
"""
        for entity_type, count in sorted(stats['entity_types'].items(), key=lambda x: x[1], reverse=True):
            summary += f"- {entity_type}: {count}\n"
        
        summary += f"\n**Relationship Types:**\n"
        for rel_type in sorted(stats['relationship_types']):
            summary += f"- {rel_type}\n"
        
        return summary

