"""
Agent Tools for LangGraph ReAct Agent
Comprehensive set of tools for Knowledge Graph operations, document search, Vespa DB, and reasoning
"""

from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from knowledge_graph import KnowledgeGraph
from kg_retriever import KGRetriever
from vespa_search import VespaSearchWrapper
import json
import re


class AgentToolkit:
    """
    Toolkit providing all tools for the ReAct agent.
    Tools are defined as instance methods and can access shared state.
    """
    
    def __init__(self, kg_retriever: KGRetriever, original_documents: str):
        """
        Initialize the agent toolkit.
        
        Args:
            kg_retriever: KGRetriever instance with built knowledge graph
            original_documents: Original document content as string
        """
        self.kg_retriever = kg_retriever
        self.kg = kg_retriever.kg
        self.original_documents = original_documents
        self.documents = kg_retriever.documents
    
    def get_tools(self) -> List:
        """
        Get all tools as LangChain tool objects.
        
        Returns:
            List of tool functions
        """
        return [
            self._search_entities,
            self._get_entity_details,
            self._get_entity_relationships,
            self._find_relationship_path,
            self._search_documents,
            self._aggregate_entity_info,
            self._detect_compliance_gaps,
            self._traverse_graph,
            self._query_kg_statistics,
        ]


@tool
def _search_entities_tool(
    entity_type: Optional[str] = None,
    value_pattern: Optional[str] = None,
    toolkit: Any = None
) -> str:
    """
    Search for entities in the knowledge graph.
    
    Args:
        entity_type: Filter by entity type (CONTROL, RISK, ASSET, REQUIREMENT, POLICY, PERSON, STANDARD). Leave empty for all types.
        value_pattern: Regex pattern to match entity values. Leave empty to get all entities of the type.
    
    Returns:
        JSON string with list of matching entities
    
    Examples:
        - search_entities(entity_type="CONTROL") - Find all controls
        - search_entities(entity_type="RISK", value_pattern="high|critical") - Find high/critical risks
        - search_entities(value_pattern="AC-.*") - Find entities matching AC-* pattern
    """
    if toolkit is None:
        return json.dumps({"error": "Toolkit not initialized"})
    
    try:
        entities = toolkit.kg.query_entities(
            entity_type=entity_type,
            value_pattern=value_pattern
        )
        
        # Format results
        results = []
        for entity in entities[:50]:  # Limit to top 50
            results.append({
                'id': entity['id'],
                'type': entity.get('entity_type', 'UNKNOWN'),
                'value': entity.get('value', ''),
                'source': entity.get('source_doc', ''),
            })
        
        return json.dumps({
            'count': len(entities),
            'showing': len(results),
            'entities': results
        }, indent=2)
    
    except Exception as e:
        return json.dumps({"error": str(e)})


def create_agent_tools(
    kg_retriever: KGRetriever,
    original_documents: str,
    vespa_wrapper: Optional[VespaSearchWrapper] = None
) -> List:
    """
    Create all agent tools with access to the knowledge graph, documents, and Vespa DB.
    
    Args:
        kg_retriever: KGRetriever instance
        original_documents: Original document content
        vespa_wrapper: Optional VespaSearchWrapper for vector search
        
    Returns:
        List of LangChain tools
    """
    
    @tool
    def search_entities(
        entity_type: Optional[str] = None,
        value_pattern: Optional[str] = None
    ) -> str:
        """
        Search for entities in the knowledge graph.
        
        Args:
            entity_type: Filter by entity type (CONTROL, RISK, ASSET, REQUIREMENT, POLICY, PERSON, STANDARD). Leave empty for all types.
            value_pattern: Regex pattern to match entity values. Leave empty to get all entities of the type.
        
        Returns:
            JSON string with list of matching entities including their IDs, types, values, and sources
        
        Examples:
            - search_entities(entity_type="CONTROL") - Find all controls
            - search_entities(entity_type="RISK", value_pattern="high|critical") - Find high/critical risks
            - search_entities(value_pattern="AC-2") - Find entities with value AC-2
        """
        try:
            entities = kg_retriever.kg.query_entities(
                entity_type=entity_type,
                value_pattern=value_pattern
            )
            
            # Format results
            results = []
            for entity in entities[:50]:  # Limit to top 50
                results.append({
                    'id': entity['id'],
                    'type': entity.get('entity_type', 'UNKNOWN'),
                    'value': entity.get('value', ''),
                    'source': entity.get('source_doc', ''),
                    'context_preview': entity.get('context', '')[:100]
                })
            
            return json.dumps({
                'count': len(entities),
                'showing': len(results),
                'entities': results
            }, indent=2)
        
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    @tool
    def get_entity_details(entity_id: str) -> str:
        """
        Get complete details about a specific entity.
        
        Args:
            entity_id: The entity ID (get this from search_entities)
        
        Returns:
            JSON string with full entity details including context, source, and all metadata
        
        Example:
            - get_entity_details(entity_id="CONTROL_AC-2")
        """
        try:
            if not kg_retriever.kg.graph.has_node(entity_id):
                return json.dumps({"error": f"Entity '{entity_id}' not found"})
            
            node_data = kg_retriever.kg.graph.nodes[entity_id]
            
            return json.dumps({
                'id': entity_id,
                'type': node_data.get('entity_type', 'UNKNOWN'),
                'value': node_data.get('value', ''),
                'context': node_data.get('context', ''),
                'source_doc': node_data.get('source_doc', ''),
                'json_path': node_data.get('json_path', ''),
            }, indent=2)
        
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    @tool
    def get_entity_relationships(
        entity_id: str,
        max_depth: int = 1
    ) -> str:
        """
        Get all entities related to a specific entity.
        
        Args:
            entity_id: The entity ID to find relationships for
            max_depth: How many relationship hops to traverse (1-3 recommended, default 1)
        
        Returns:
            JSON string with related entities and their relationship types
        
        Example:
            - get_entity_relationships(entity_id="CONTROL_AC-2", max_depth=1)
            - get_entity_relationships(entity_id="RISK_R-001", max_depth=2)
        """
        try:
            related = kg_retriever.kg.get_related_entities(entity_id, max_depth=max_depth)
            
            # Format results
            results = []
            for rel in related[:30]:  # Limit to 30
                results.append({
                    'related_id': rel['id'],
                    'related_type': rel.get('entity_type', 'UNKNOWN'),
                    'related_value': rel.get('value', ''),
                    'relationship_type': rel.get('relation_type', 'RELATES_TO'),
                    'direction': rel.get('direction', 'unknown'),
                    'depth': rel.get('depth', 0),
                })
            
            return json.dumps({
                'source_entity': entity_id,
                'total_related': len(related),
                'showing': len(results),
                'relationships': results
            }, indent=2)
        
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    @tool
    def find_relationship_path(
        source_entity_id: str,
        target_entity_id: str
    ) -> str:
        """
        Find the connection path between two entities.
        
        Args:
            source_entity_id: Starting entity ID
            target_entity_id: Target entity ID
        
        Returns:
            JSON string with the path(s) connecting the two entities
        
        Example:
            - find_relationship_path(source_entity_id="CONTROL_AC-2", target_entity_id="STANDARD_ISO_27001")
        """
        try:
            import networkx as nx
            
            if not kg_retriever.kg.graph.has_node(source_entity_id):
                return json.dumps({"error": f"Source entity '{source_entity_id}' not found"})
            if not kg_retriever.kg.graph.has_node(target_entity_id):
                return json.dumps({"error": f"Target entity '{target_entity_id}' not found"})
            
            # Find shortest path using NetworkX
            try:
                # Try both directed and undirected paths
                path = None
                try:
                    path = nx.shortest_path(kg_retriever.kg.graph, source_entity_id, target_entity_id)
                except nx.NetworkXNoPath:
                    # Try undirected
                    undirected = kg_retriever.kg.graph.to_undirected()
                    path = nx.shortest_path(undirected, source_entity_id, target_entity_id)
                
                if path:
                    # Build path with relationship details
                    path_details = []
                    for i in range(len(path) - 1):
                        from_id = path[i]
                        to_id = path[i + 1]
                        
                        # Get relationship type
                        rel_type = 'RELATES_TO'
                        if kg_retriever.kg.graph.has_edge(from_id, to_id):
                            edge_data = kg_retriever.kg.graph.get_edge_data(from_id, to_id)
                            rel_type = list(edge_data.values())[0].get('relation_type', 'RELATES_TO')
                        
                        # Get entity details
                        from_data = kg_retriever.kg.graph.nodes[from_id]
                        to_data = kg_retriever.kg.graph.nodes[to_id]
                        
                        path_details.append({
                            'step': i + 1,
                            'from': {
                                'id': from_id,
                                'type': from_data.get('entity_type'),
                                'value': from_data.get('value'),
                            },
                            'relationship': rel_type,
                            'to': {
                                'id': to_id,
                                'type': to_data.get('entity_type'),
                                'value': to_data.get('value'),
                            }
                        })
                    
                    return json.dumps({
                        'path_found': True,
                        'path_length': len(path) - 1,
                        'path': path_details
                    }, indent=2)
                
            except nx.NetworkXNoPath:
                return json.dumps({
                    'path_found': False,
                    'message': 'No connection path found between these entities'
                })
        
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    @tool
    def search_documents(query: str) -> str:
        """
        Search the original document content for specific text or information.
        
        Args:
            query: Search query or keywords
        
        Returns:
            JSON string with matching document snippets and sources
        
        Example:
            - search_documents(query="password policy")
            - search_documents(query="encryption requirements")
        """
        try:
            # Simple text search in original documents
            results = []
            
            # Split documents by common separators
            doc_sections = re.split(r'={80}', original_documents)
            
            query_lower = query.lower()
            for section in doc_sections:
                if query_lower in section.lower():
                    # Extract document name
                    doc_name_match = re.search(r'Document:\s*([^\n]+)', section)
                    doc_name = doc_name_match.group(1) if doc_name_match else 'Unknown'
                    
                    # Find the snippet with context
                    lines = section.split('\n')
                    for i, line in enumerate(lines):
                        if query_lower in line.lower():
                            # Get context (2 lines before and after)
                            start = max(0, i - 2)
                            end = min(len(lines), i + 3)
                            snippet = '\n'.join(lines[start:end])
                            
                            results.append({
                                'source': doc_name,
                                'snippet': snippet.strip(),
                                'match_line': line.strip()
                            })
                            
                            if len(results) >= 10:  # Limit results
                                break
                
                if len(results) >= 10:
                    break
            
            return json.dumps({
                'query': query,
                'matches_found': len(results),
                'results': results
            }, indent=2)
        
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    @tool
    def aggregate_entity_info(entity_ids: str) -> str:
        """
        Collect and summarize information across multiple entities.
        
        Args:
            entity_ids: Comma-separated list of entity IDs
        
        Returns:
            JSON string with aggregated information about all entities
        
        Example:
            - aggregate_entity_info(entity_ids="CONTROL_AC-2,CONTROL_AU-2,CONTROL_CM-5")
        """
        try:
            ids = [eid.strip() for eid in entity_ids.split(',')]
            
            aggregated = []
            for entity_id in ids:
                if kg_retriever.kg.graph.has_node(entity_id):
                    node_data = kg_retriever.kg.graph.nodes[entity_id]
                    
                    # Get relationships count
                    in_degree = kg_retriever.kg.graph.in_degree(entity_id)
                    out_degree = kg_retriever.kg.graph.out_degree(entity_id)
                    
                    aggregated.append({
                        'id': entity_id,
                        'type': node_data.get('entity_type'),
                        'value': node_data.get('value'),
                        'source': node_data.get('source_doc'),
                        'relationships_in': in_degree,
                        'relationships_out': out_degree,
                        'context_preview': node_data.get('context', '')[:150]
                    })
            
            return json.dumps({
                'requested': len(ids),
                'found': len(aggregated),
                'entities': aggregated
            }, indent=2)
        
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    @tool
    def detect_compliance_gaps(
        entity_type: str = "RISK",
        relationship_type: str = "MITIGATES"
    ) -> str:
        """
        Identify entities that lack expected relationships (gaps in coverage).
        
        Args:
            entity_type: Type of entity to check (RISK or REQUIREMENT typically)
            relationship_type: Expected relationship type (e.g., MITIGATES for risks, IMPLEMENTS for requirements)
        
        Returns:
            JSON string with entities that lack the expected relationships
        
        Example:
            - detect_compliance_gaps(entity_type="RISK", relationship_type="MITIGATES")
            - detect_compliance_gaps(entity_type="REQUIREMENT", relationship_type="IMPLEMENTS")
        """
        try:
            # Get all entities of the specified type
            all_entities = kg_retriever.kg.query_entities(entity_type=entity_type)
            
            gaps = []
            for entity in all_entities:
                entity_id = entity['id']
                
                # Check if this entity has any incoming relationships of the specified type
                has_relationship = False
                if kg_retriever.kg.graph.has_node(entity_id):
                    for predecessor in kg_retriever.kg.graph.predecessors(entity_id):
                        edge_data = kg_retriever.kg.graph.get_edge_data(predecessor, entity_id)
                        if edge_data:
                            for edge in edge_data.values():
                                if edge.get('relation_type') == relationship_type:
                                    has_relationship = True
                                    break
                        if has_relationship:
                            break
                
                if not has_relationship:
                    gaps.append({
                        'id': entity_id,
                        'type': entity.get('entity_type'),
                        'value': entity.get('value'),
                        'source': entity.get('source_doc'),
                        'missing_relationship': relationship_type,
                        'context_preview': entity.get('context', '')[:100]
                    })
            
            return json.dumps({
                'total_entities_checked': len(all_entities),
                'gaps_found': len(gaps),
                'entity_type': entity_type,
                'missing_relationship_type': relationship_type,
                'gaps': gaps[:20]  # Limit to 20
            }, indent=2)
        
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    @tool
    def traverse_graph(
        start_entity_id: str,
        max_depth: int = 2,
        relationship_filter: Optional[str] = None
    ) -> str:
        """
        Perform deep traversal of the knowledge graph from a starting entity.
        
        Args:
            start_entity_id: Entity ID to start traversal from
            max_depth: Maximum depth to traverse (1-3 recommended)
            relationship_filter: Optional filter for relationship types (comma-separated)
        
        Returns:
            JSON string with all entities discovered in traversal
        
        Example:
            - traverse_graph(start_entity_id="CONTROL_AC-2", max_depth=2)
            - traverse_graph(start_entity_id="RISK_R-001", max_depth=2, relationship_filter="MITIGATES,IMPLEMENTS")
        """
        try:
            if not kg_retriever.kg.graph.has_node(start_entity_id):
                return json.dumps({"error": f"Entity '{start_entity_id}' not found"})
            
            # Parse relationship filter
            rel_filters = None
            if relationship_filter:
                rel_filters = set(r.strip() for r in relationship_filter.split(','))
            
            # BFS traversal
            visited = set()
            discovered = []
            queue = [(start_entity_id, 0)]
            
            while queue:
                current_id, depth = queue.pop(0)
                
                if current_id in visited or depth > max_depth:
                    continue
                
                visited.add(current_id)
                
                # Get node data
                node_data = kg_retriever.kg.graph.nodes[current_id]
                
                discovered.append({
                    'id': current_id,
                    'type': node_data.get('entity_type'),
                    'value': node_data.get('value'),
                    'depth': depth,
                    'source': node_data.get('source_doc')
                })
                
                # Add neighbors
                for neighbor in kg_retriever.kg.graph.successors(current_id):
                    if neighbor not in visited:
                        # Check relationship filter
                        if rel_filters:
                            edge_data = kg_retriever.kg.graph.get_edge_data(current_id, neighbor)
                            rel_type = list(edge_data.values())[0].get('relation_type', '')
                            if rel_type not in rel_filters:
                                continue
                        
                        queue.append((neighbor, depth + 1))
            
            return json.dumps({
                'start_entity': start_entity_id,
                'max_depth': max_depth,
                'entities_discovered': len(discovered),
                'entities': discovered[:50]  # Limit to 50
            }, indent=2)
        
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    @tool
    def query_kg_statistics() -> str:
        """
        Get statistics about the knowledge graph.
        
        Returns:
            JSON string with graph statistics including entity counts, relationship counts, and types
        
        Example:
            - query_kg_statistics()
        """
        try:
            stats = kg_retriever.get_statistics()
            
            return json.dumps({
                'documents_processed': stats.get('document_count', 0),
                'total_entities': stats.get('entity_count', 0),
                'total_relationships': stats.get('relationship_count', 0),
                'entity_types': stats.get('entity_types', {}),
                'relationship_types': stats.get('relationship_types', []),
                'graph_density': stats.get('graph_density', 0),
                'connected_components': stats.get('connected_components', 0)
            }, indent=2)
        
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    # Vespa vector store search tool (optional)
    if vespa_wrapper:
        @tool
        def search_vespa_db(
            query: str,
            top_k: int = 10,
            filters_json: Optional[str] = None
        ) -> str:
            """
            Search the Vespa vector database for additional context and information.
            
            Args:
                query: Search query or question
                top_k: Number of results to return (default 10)
                filters_json: Optional JSON string with filters (e.g., '{"field_1_s": "demo"}')
            
            Returns:
                JSON string with search results from Vespa DB
            
            Examples:
                - search_vespa_db(query="What is the ingestion demo?", filters_json='{"field_1_s": "demo"}')
                - search_vespa_db(query="apple's net earning in 2024 Q3", top_k=10)
                - search_vespa_db(query="security controls for database")
            
            Use this tool when:
            - You need additional context beyond uploaded documents
            - Looking for specific information in the broader knowledge base
            - Documents don't contain the needed information
            """
            try:
                # Parse filters if provided
                filters = None
                if filters_json:
                    try:
                        filters = json.loads(filters_json)
                    except json.JSONDecodeError:
                        return json.dumps({
                            "error": f"Invalid filters JSON: {filters_json}"
                        })
                
                # Search Vespa
                result = vespa_wrapper.search(
                    query=query,
                    top_k=top_k,
                    filters=filters
                )
                
                # Format for LLM
                if result.get('success'):
                    formatted = vespa_wrapper.format_results_for_llm(result)
                    return json.dumps({
                        'success': True,
                        'query': query,
                        'results_count': result.get('count', 0),
                        'formatted_results': formatted,
                        'raw_results': result.get('results', [])
                    }, indent=2)
                else:
                    return json.dumps({
                        'success': False,
                        'error': result.get('error', 'Unknown error')
                    })
            
            except Exception as e:
                return json.dumps({"error": str(e)})
    
    # Return all tools
    tools = [
        search_entities,
        get_entity_details,
        get_entity_relationships,
        find_relationship_path,
        search_documents,
        aggregate_entity_info,
        detect_compliance_gaps,
        traverse_graph,
        query_kg_statistics,
    ]
    
    # Add Vespa tool if available
    if vespa_wrapper:
        tools.append(search_vespa_db)
    
    return tools

