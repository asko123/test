"""
Knowledge Graph Module
Builds and manages a knowledge graph from document content for better relationship tracking
"""

import networkx as nx
import json
import re
from typing import Dict, List, Tuple, Any, Set
from collections import defaultdict
from datetime import datetime


class KnowledgeGraph:
    """Knowledge Graph for storing and querying document entities and relationships."""
    
    # Define entity types and their patterns
    ENTITY_PATTERNS = {
        'CONTROL': [
            r'control[_\s]+(?:id|ID|number|#)?[:\s]*([A-Z0-9\-\.]+)',
            r'(?:control|CONTROL)\s+([A-Z]{2,}[_\-]?\d{3,})',
            r'(?:AC|AU|CM|IA|IR|MA|PE|PS|RA|SA|SC|SI|SR|AT|CA|CP|IA|MP|PL|PM|PT)-\d{1,3}(?:\(\d+\))?',
        ],
        'RISK': [
            r'risk[_\s]+(?:id|ID|number|#)?[:\s]*([A-Z0-9\-\.]+)',
            r'(?:high|medium|low|critical)\s+risk',
            r'risk[_\s]+level[:\s]*(high|medium|low|critical)',
        ],
        'ASSET': [
            r'asset[_\s]+(?:type|id|name)?[:\s]*([A-Za-z0-9\-_\s]+)',
            r'(?:server|database|application|network|endpoint|cloud)',
        ],
        'REQUIREMENT': [
            r'requirement[_\s]+(?:id|ID|number)?[:\s]*([A-Z0-9\-\.]+)',
            r'(?:MUST|SHALL|SHOULD|MAY)\s+([a-z][^.]{10,80})',
        ],
        'POLICY': [
            r'policy[_\s]+(?:id|ID|number|name)?[:\s]*([A-Za-z0-9\-_\s]+)',
            r'(?:security|access|data|privacy|compliance)\s+policy',
        ],
        'PERSON': [
            r'(?:responsible|owner|assignee)[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'(?:manager|director|officer|analyst)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        ],
        'STANDARD': [
            r'(?:NIST|ISO|SOC|PCI|HIPAA|GDPR|CIS|COBIT)\s*[:\-]?\s*([A-Z0-9\-\.]+)?',
            r'(?:framework|standard)[:\s]+([A-Z][A-Za-z0-9\-_\s]+)',
        ],
    }
    
    def __init__(self):
        """Initialize the Knowledge Graph."""
        self.graph = nx.MultiDiGraph()
        self.entity_index = defaultdict(set)  # Type -> Set of entity IDs
        self.relationship_types = set()
        self.metadata = {
            'created_at': datetime.now().isoformat(),
            'document_count': 0,
            'entity_count': 0,
            'relationship_count': 0,
        }
        
    def extract_entities_from_text(self, text: str, doc_name: str) -> List[Dict[str, Any]]:
        """
        Extract entities from text using pattern matching and NLP.
        
        Args:
            text: Text to extract entities from
            doc_name: Name of the source document
            
        Returns:
            List of extracted entities
        """
        entities = []
        seen_entities = set()
        
        # Extract using patterns
        for entity_type, patterns in self.ENTITY_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    entity_value = match.group(1) if match.groups() else match.group(0)
                    entity_value = entity_value.strip()
                    
                    # Create a unique identifier
                    entity_id = f"{entity_type}_{entity_value.replace(' ', '_')[:50]}"
                    
                    # Avoid duplicates
                    if entity_id not in seen_entities:
                        seen_entities.add(entity_id)
                        
                        # Get context around the match
                        start = max(0, match.start() - 100)
                        end = min(len(text), match.end() + 100)
                        context = text[start:end].replace('\n', ' ')
                        
                        entities.append({
                            'id': entity_id,
                            'type': entity_type,
                            'value': entity_value,
                            'context': context,
                            'source_doc': doc_name,
                            'position': match.start(),
                        })
        
        return entities
    
    def extract_entities_from_json(self, json_data: Any, doc_name: str, path: str = '') -> List[Dict[str, Any]]:
        """
        Extract entities from structured JSON data.
        
        Args:
            json_data: JSON data (dict, list, or primitive)
            doc_name: Name of the source document
            path: Current path in JSON structure
            
        Returns:
            List of extracted entities
        """
        entities = []
        
        # Keywords that indicate entity types
        entity_keywords = {
            'CONTROL': ['control', 'controls', 'control_id', 'control_name'],
            'RISK': ['risk', 'risks', 'risk_id', 'risk_level', 'severity'],
            'ASSET': ['asset', 'assets', 'asset_type', 'resource'],
            'REQUIREMENT': ['requirement', 'requirements', 'req_id'],
            'POLICY': ['policy', 'policies', 'policy_id'],
            'PERSON': ['owner', 'responsible', 'assignee', 'manager'],
            'STANDARD': ['standard', 'framework', 'compliance'],
        }
        
        if isinstance(json_data, dict):
            for key, value in json_data.items():
                current_path = f"{path}.{key}" if path else key
                
                # Check if this key indicates an entity type
                entity_type = None
                for etype, keywords in entity_keywords.items():
                    if any(kw in key.lower() for kw in keywords):
                        entity_type = etype
                        break
                
                # Extract entity if we found a type and value is simple
                if entity_type and isinstance(value, (str, int, float)):
                    entity_id = f"{entity_type}_{str(value).replace(' ', '_')[:50]}"
                    entities.append({
                        'id': entity_id,
                        'type': entity_type,
                        'value': str(value),
                        'context': f"From JSON path: {current_path}",
                        'source_doc': doc_name,
                        'json_path': current_path,
                    })
                
                # Recurse into nested structures
                if isinstance(value, (dict, list)):
                    entities.extend(self.extract_entities_from_json(value, doc_name, current_path))
        
        elif isinstance(json_data, list):
            for i, item in enumerate(json_data):
                current_path = f"{path}[{i}]"
                entities.extend(self.extract_entities_from_json(item, doc_name, current_path))
        
        return entities
    
    def detect_relationships(self, entities: List[Dict[str, Any]], text: str) -> List[Tuple[str, str, str, Dict]]:
        """
        Detect relationships between entities based on proximity and patterns.
        
        Args:
            entities: List of extracted entities
            text: Original text
            
        Returns:
            List of (source_id, target_id, relation_type, metadata) tuples
        """
        relationships = []
        
        # Relationship patterns
        relation_patterns = {
            'IMPLEMENTS': [r'implements?', r'satisfies', r'addresses', r'covers'],
            'MITIGATES': [r'mitigates?', r'reduces', r'controls', r'prevents'],
            'REQUIRES': [r'requires?', r'needs', r'depends on', r'mandates'],
            'OWNS': [r'owned by', r'managed by', r'responsible for'],
            'APPLIES_TO': [r'applies to', r'applicable to', r'affects'],
            'RELATES_TO': [r'related to', r'associated with', r'linked to'],
        }
        
        # Sort entities by position for proximity detection
        sorted_entities = sorted(entities, key=lambda e: e.get('position', 0))
        
        # Check for proximity-based relationships
        for i, entity1 in enumerate(sorted_entities):
            for entity2 in sorted_entities[i+1:i+6]:  # Check next 5 entities
                pos1 = entity1.get('position', 0)
                pos2 = entity2.get('position', 0)
                
                # If entities are close in text (within 200 chars)
                if abs(pos2 - pos1) < 200:
                    # Extract text between entities
                    start = min(pos1, pos2)
                    end = max(pos1, pos2) + len(entity1.get('value', ''))
                    between_text = text[start:end].lower()
                    
                    # Check for relationship indicators
                    for rel_type, patterns in relation_patterns.items():
                        if any(re.search(pattern, between_text) for pattern in patterns):
                            relationships.append((
                                entity1['id'],
                                entity2['id'],
                                rel_type,
                                {
                                    'evidence': between_text[:100],
                                    'confidence': 0.8,
                                }
                            ))
                            break
                    else:
                        # If no specific pattern, add generic relationship
                        relationships.append((
                            entity1['id'],
                            entity2['id'],
                            'RELATES_TO',
                            {
                                'evidence': 'proximity',
                                'confidence': 0.5,
                            }
                        ))
        
        return relationships
    
    def add_entity(self, entity: Dict[str, Any]):
        """
        Add an entity to the knowledge graph.
        
        Args:
            entity: Entity dictionary with id, type, value, context, etc.
        """
        entity_id = entity['id']
        
        # Add node to graph
        self.graph.add_node(
            entity_id,
            entity_type=entity['type'],
            value=entity['value'],
            context=entity.get('context', ''),
            source_doc=entity.get('source_doc', ''),
            json_path=entity.get('json_path', ''),
        )
        
        # Update entity index
        self.entity_index[entity['type']].add(entity_id)
        
        # Update metadata
        self.metadata['entity_count'] = len(self.graph.nodes)
    
    def add_relationship(self, source_id: str, target_id: str, relation_type: str, metadata: Dict = None):
        """
        Add a relationship between two entities.
        
        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            relation_type: Type of relationship
            metadata: Additional relationship metadata
        """
        if not self.graph.has_node(source_id) or not self.graph.has_node(target_id):
            return
        
        # Add edge to graph
        self.graph.add_edge(
            source_id,
            target_id,
            relation_type=relation_type,
            **(metadata or {})
        )
        
        # Update tracking
        self.relationship_types.add(relation_type)
        self.metadata['relationship_count'] = len(self.graph.edges)
    
    def build_from_documents(self, documents: List[Dict[str, Any]]):
        """
        Build knowledge graph from multiple documents.
        
        Args:
            documents: List of document dicts with 'name', 'content', and optional 'json_data'
        """
        all_entities = []
        
        for doc in documents:
            doc_name = doc.get('name', 'unknown')
            
            # Extract entities from text content
            if 'content' in doc:
                entities = self.extract_entities_from_text(doc['content'], doc_name)
                all_entities.extend(entities)
                
                # Detect and add relationships
                relationships = self.detect_relationships(entities, doc['content'])
                for src, tgt, rel_type, meta in relationships:
                    # Add entities first
                    for entity in entities:
                        if entity['id'] in (src, tgt):
                            self.add_entity(entity)
                    
                    # Add relationship
                    self.add_relationship(src, tgt, rel_type, meta)
            
            # Extract entities from JSON data
            if 'json_data' in doc:
                json_entities = self.extract_entities_from_json(doc['json_data'], doc_name)
                all_entities.extend(json_entities)
        
        # Add all entities to graph
        for entity in all_entities:
            self.add_entity(entity)
        
        # Update metadata
        self.metadata['document_count'] = len(documents)
    
    def query_entities(self, entity_type: str = None, value_pattern: str = None) -> List[Dict[str, Any]]:
        """
        Query entities from the graph.
        
        Args:
            entity_type: Filter by entity type
            value_pattern: Regex pattern to match entity values
            
        Returns:
            List of matching entity nodes
        """
        results = []
        
        for node_id in self.graph.nodes:
            node_data = self.graph.nodes[node_id]
            
            # Filter by type
            if entity_type and node_data.get('entity_type') != entity_type:
                continue
            
            # Filter by value pattern
            if value_pattern:
                if not re.search(value_pattern, node_data.get('value', ''), re.IGNORECASE):
                    continue
            
            results.append({
                'id': node_id,
                **node_data
            })
        
        return results
    
    def get_related_entities(self, entity_id: str, max_depth: int = 2) -> List[Dict[str, Any]]:
        """
        Get entities related to a given entity.
        
        Args:
            entity_id: Entity ID to start from
            max_depth: Maximum depth of relationships to traverse
            
        Returns:
            List of related entities with relationship information
        """
        if not self.graph.has_node(entity_id):
            return []
        
        related = []
        visited = set()
        
        # BFS traversal
        queue = [(entity_id, 0, [])]
        
        while queue:
            current_id, depth, path = queue.pop(0)
            
            if current_id in visited or depth > max_depth:
                continue
            
            visited.add(current_id)
            
            # Get all neighbors (both incoming and outgoing)
            neighbors = list(self.graph.successors(current_id)) + list(self.graph.predecessors(current_id))
            
            for neighbor_id in neighbors:
                if neighbor_id not in visited:
                    # Get relationship info
                    if self.graph.has_edge(current_id, neighbor_id):
                        edge_data = self.graph.get_edge_data(current_id, neighbor_id)
                        relation_type = list(edge_data.values())[0].get('relation_type', 'RELATES_TO')
                        direction = 'outgoing'
                    else:
                        edge_data = self.graph.get_edge_data(neighbor_id, current_id)
                        relation_type = list(edge_data.values())[0].get('relation_type', 'RELATES_TO')
                        direction = 'incoming'
                    
                    neighbor_data = self.graph.nodes[neighbor_id]
                    related.append({
                        'id': neighbor_id,
                        'depth': depth + 1,
                        'relation_type': relation_type,
                        'direction': direction,
                        'path': path + [current_id],
                        **neighbor_data
                    })
                    
                    queue.append((neighbor_id, depth + 1, path + [current_id]))
        
        return related
    
    def get_context_for_query(self, query: str, top_k: int = 10) -> Dict[str, Any]:
        """
        Get relevant context from the knowledge graph for a query.
        
        Args:
            query: User query
            top_k: Number of top entities to return
            
        Returns:
            Dictionary with relevant entities, relationships, and context
        """
        # Extract potential entity mentions from query
        query_lower = query.lower()
        relevant_entities = []
        
        # Find entities mentioned in query
        for node_id in self.graph.nodes:
            node_data = self.graph.nodes[node_id]
            value = node_data.get('value', '').lower()
            
            # Check if entity is mentioned in query
            if value and value in query_lower:
                relevant_entities.append({
                    'id': node_id,
                    'relevance_score': 1.0,
                    **node_data
                })
        
        # If no direct matches, use keyword matching
        if not relevant_entities:
            query_keywords = set(re.findall(r'\b\w{4,}\b', query_lower))
            
            for node_id in self.graph.nodes:
                node_data = self.graph.nodes[node_id]
                value = node_data.get('value', '').lower()
                context = node_data.get('context', '').lower()
                
                # Calculate relevance score based on keyword matches
                combined_text = f"{value} {context}"
                matches = sum(1 for kw in query_keywords if kw in combined_text)
                
                if matches > 0:
                    relevant_entities.append({
                        'id': node_id,
                        'relevance_score': matches / len(query_keywords),
                        **node_data
                    })
        
        # Sort by relevance
        relevant_entities.sort(key=lambda x: x['relevance_score'], reverse=True)
        relevant_entities = relevant_entities[:top_k]
        
        # Get relationships for top entities
        relationships = []
        for entity in relevant_entities:
            related = self.get_related_entities(entity['id'], max_depth=1)
            relationships.extend(related)
        
        # Build context summary
        context_summary = {
            'entities': relevant_entities,
            'relationships': relationships,
            'entity_types': list(set(e.get('entity_type') for e in relevant_entities)),
            'relationship_types': list(set(r.get('relation_type') for r in relationships)),
            'total_entities': len(relevant_entities),
            'total_relationships': len(relationships),
        }
        
        return context_summary
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge graph statistics."""
        return {
            **self.metadata,
            'entity_types': {etype: len(entities) for etype, entities in self.entity_index.items()},
            'relationship_types': list(self.relationship_types),
            'graph_density': nx.density(self.graph),
            'connected_components': nx.number_weakly_connected_components(self.graph),
        }
    
    def export_for_llm(self, context: Dict[str, Any]) -> str:
        """
        Export knowledge graph context in a format optimized for LLM consumption.
        
        Args:
            context: Context dictionary from get_context_for_query
            
        Returns:
            Formatted string for LLM
        """
        output = []
        
        # Header
        output.append("=== KNOWLEDGE GRAPH CONTEXT ===\n")
        
        # Entities
        if context['entities']:
            output.append("## RELEVANT ENTITIES:")
            for i, entity in enumerate(context['entities'], 1):
                output.append(f"\n{i}. {entity['entity_type']}: {entity['value']}")
                output.append(f"   Source: {entity.get('source_doc', 'unknown')}")
                if entity.get('context'):
                    output.append(f"   Context: {entity['context'][:150]}...")
                if entity.get('json_path'):
                    output.append(f"   JSON Path: {entity['json_path']}")
        
        # Relationships
        if context['relationships']:
            output.append("\n\n## RELATIONSHIPS:")
            seen_relations = set()
            for i, rel in enumerate(context['relationships'][:20], 1):  # Limit to top 20
                rel_key = (rel['id'], rel['relation_type'])
                if rel_key not in seen_relations:
                    seen_relations.add(rel_key)
                    output.append(f"\n{i}. {rel['relation_type']} -> {rel['entity_type']}: {rel['value']}")
                    if rel.get('evidence'):
                        output.append(f"   Evidence: {rel['evidence'][:100]}")
        
        # Summary
        output.append(f"\n\n## SUMMARY:")
        output.append(f"- Total Entities Found: {context['total_entities']}")
        output.append(f"- Entity Types: {', '.join(context['entity_types'])}")
        output.append(f"- Total Relationships: {context['total_relationships']}")
        output.append(f"- Relationship Types: {', '.join(context['relationship_types'][:5])}")
        
        output.append("\n" + "="*50 + "\n")
        
        return "\n".join(output)

