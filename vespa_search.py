"""
Vespa Vector Store Search Wrapper
Provides search capabilities against Vespa DB for additional context
"""

from typing import List, Dict, Any, Optional
import json


class VespaSearchWrapper:
    """
    Wrapper for Goldman Sachs Vespa Vector Store.
    Provides search capabilities for agent and fallback when no documents uploaded.
    """
    
    def __init__(
        self,
        schema_id: str = "tech_risk_ai",
        env: str = "uat"
    ):
        """
        Initialize Vespa search wrapper.
        
        Args:
            schema_id: Vespa schema identifier
            env: Environment (dev, uat, or prod)
        """
        self.schema_id = schema_id
        self.env = env
        self.vector_store = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the Vespa vector store connection."""
        try:
            from goldmansachs.awm_genai import VectorStore
            self.vector_store = VectorStore(schema_id=self.schema_id, env=self.env)
        except ImportError as e:
            raise ImportError(
                f"VectorStore not available: {e}. "
                "Ensure goldmansachs.awm_genai package is installed."
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Vespa connection: {e}")
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        Search Vespa vector store.
        
        Args:
            query: Search query
            top_k: Number of results to return
            filters: Optional filters (e.g., {"field_1_s": "demo"})
            page: Page number for pagination
            
        Returns:
            Dictionary with search results
        """
        if not self.vector_store:
            return {
                'success': False,
                'error': 'Vespa vector store not initialized',
                'results': []
            }
        
        try:
            if filters:
                result = self.vector_store.search(query, filters=filters)
            else:
                result = self.vector_store.search(query, top_k=top_k, page=page)
            
            return {
                'success': True,
                'query': query,
                'results': result,
                'count': len(result) if isinstance(result, list) else 1
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'results': []
            }
    
    def format_results_for_llm(self, search_result: Dict[str, Any]) -> str:
        """
        Format Vespa search results for LLM consumption.
        
        Args:
            search_result: Result from search()
            
        Returns:
            Formatted string for LLM
        """
        if not search_result.get('success'):
            return f"Search failed: {search_result.get('error', 'Unknown error')}"
        
        results = search_result.get('results', [])
        
        if not results:
            return f"No results found for query: {search_result.get('query')}"
        
        # Format results
        output = []
        output.append("=== VESPA SEARCH RESULTS ===\n")
        output.append(f"Query: {search_result.get('query')}")
        output.append(f"Results found: {search_result.get('count', 0)}\n")
        
        # Format each result
        if isinstance(results, list):
            for i, result in enumerate(results[:10], 1):  # Limit to top 10
                output.append(f"\n[Result {i}]")
                
                # Handle different result formats
                if isinstance(result, dict):
                    for key, value in result.items():
                        # Truncate long values
                        value_str = str(value)
                        if len(value_str) > 200:
                            value_str = value_str[:200] + "..."
                        output.append(f"  {key}: {value_str}")
                else:
                    output.append(f"  {str(result)[:500]}")
        else:
            # Single result
            output.append(f"\n{str(results)[:1000]}")
        
        output.append("\n" + "="*50 + "\n")
        
        return "\n".join(output)
    
    def is_available(self) -> bool:
        """Check if Vespa is available and connected."""
        return self.vector_store is not None
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Get information about the Vespa schema."""
        return {
            'schema_id': self.schema_id,
            'env': self.env,
            'available': self.is_available()
        }


def create_vespa_wrapper(
    schema_id: str = "tech_risk_ai",
    env: str = "uat"
) -> Optional[VespaSearchWrapper]:
    """
    Factory function to create Vespa wrapper with error handling.
    
    Args:
        schema_id: Vespa schema ID
        env: Environment
        
    Returns:
        VespaSearchWrapper instance or None if unavailable
    """
    try:
        return VespaSearchWrapper(schema_id=schema_id, env=env)
    except Exception as e:
        print(f"[WARNING] Vespa not available: {e}")
        return None

