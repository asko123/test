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
        env: str = "uat",
        gssso_token: Optional[str] = None,
        api_key: Optional[str] = None,
        ranking_profile: str = "dense"
    ):
        """
        Initialize Vespa search wrapper.
        
        Args:
            schema_id: Vespa schema identifier
            env: Environment (dev, uat, or prod)
            gssso_token: Optional GSSSO authentication token
            api_key: Optional API key for authentication
            ranking_profile: Vespa ranking profile (default: dense)
        """
        self.schema_id = schema_id
        self.env = env
        self.gssso_token = gssso_token
        self.api_key = api_key
        self.ranking_profile = ranking_profile
        self.vector_store = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the Vespa vector store connection."""
        try:
            from goldmansachs.awm_genai import VectorStore
            self.vector_store = VectorStore(schema_id=self.schema_id, env=self.env)
            print(f"[INFO] Vespa initialized: schema={self.schema_id}, env={self.env}")
        except ImportError as e:
            raise ImportError(
                f"VectorStore not available: {e}. "
                "Ensure goldmansachs.awm_genai package is installed."
            )
        except Exception as e:
            print(f"[ERROR] Vespa initialization failed: {e}")
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
                'results': [],
                'error_type': 'initialization_error'
            }
        
        try:
            print(f"[DEBUG] Vespa search: query='{query[:50]}...', top_k={top_k}, filters={filters}")
            print(f"[DEBUG] Using ranking_profile={self.ranking_profile}, gssso={'***' if self.gssso_token else 'None'}")
            
            # Build search parameters
            search_params = {
                'query': query,
                'top_k': top_k,
                'page': page,
                'ranking_profile': self.ranking_profile
            }
            
            if filters:
                search_params['filters'] = filters
            
            if self.gssso_token:
                search_params['gssso'] = self.gssso_token
            
            if self.api_key:
                search_params['x_api_key'] = self.api_key
            
            # Perform search
            result = self.vector_store.search(**search_params)
            
            print(f"[DEBUG] Vespa search successful, results: {type(result)}")
            
            return {
                'success': True,
                'query': query,
                'results': result,
                'count': len(result) if isinstance(result, list) else 1
            }
        
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            
            print(f"[ERROR] Vespa search failed: {error_type}: {error_msg}")
            
            # Provide helpful error messages based on error type
            if "500" in error_msg or "Internal Server Error" in error_msg:
                helpful_msg = (
                    f"Vespa 500 error - Possible causes:\n"
                    f"1. Schema '{self.schema_id}' may not exist in '{self.env}' environment\n"
                    f"2. Query format may be incompatible with schema\n"
                    f"3. Authentication/permissions issue\n"
                    f"4. Vespa service may be down\n"
                    f"Suggested fixes:\n"
                    f"- Verify schema ID is correct: '{self.schema_id}'\n"
                    f"- Try different environment (dev/uat/prod)\n"
                    f"- Check Vespa service status\n"
                    f"- Simplify your query"
                )
            elif "401" in error_msg or "403" in error_msg or "Unauthorized" in error_msg:
                helpful_msg = "Authentication error - Check your credentials and permissions"
            elif "404" in error_msg:
                helpful_msg = f"Schema '{self.schema_id}' not found in '{self.env}' environment"
            else:
                helpful_msg = error_msg
            
            return {
                'success': False,
                'error': helpful_msg,
                'error_type': error_type,
                'results': [],
                'query': query
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
            error_msg = search_result.get('error', 'Unknown error')
            return f"=== VESPA SEARCH ERROR ===\n\n{error_msg}\n\n" + "="*50
        
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
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test Vespa connection with a simple query.
        
        Returns:
            Dictionary with connection test results
        """
        if not self.vector_store:
            return {
                'success': False,
                'error': 'Vector store not initialized'
            }
        
        try:
            # Try a simple test search with auth params
            search_params = {
                'query': 'test',
                'top_k': 1,
                'ranking_profile': self.ranking_profile
            }
            
            if self.gssso_token:
                search_params['gssso'] = self.gssso_token
            
            if self.api_key:
                search_params['x_api_key'] = self.api_key
            
            test_result = self.vector_store.search(**search_params)
            return {
                'success': True,
                'message': 'Connection successful',
                'schema_id': self.schema_id,
                'env': self.env
            }
        except Exception as e:
            error_msg = str(e)
            
            # Parse error for helpful feedback
            if "500" in error_msg:
                suggestion = f"Schema '{self.schema_id}' may not exist in '{self.env}'. Try: 'dev', 'uat', or 'prod'"
            elif "401" in error_msg or "403" in error_msg:
                suggestion = "Authentication issue - check your credentials"
            elif "404" in error_msg:
                suggestion = f"Schema '{self.schema_id}' not found - verify the schema name"
            else:
                suggestion = "Check Vespa service status and schema configuration"
            
            return {
                'success': False,
                'error': error_msg,
                'suggestion': suggestion,
                'schema_id': self.schema_id,
                'env': self.env
            }
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Get information about the Vespa schema."""
        return {
            'schema_id': self.schema_id,
            'env': self.env,
            'available': self.is_available()
        }


def create_vespa_wrapper(
    schema_id: str = "tech_risk_ai",
    env: str = "uat",
    gssso_token: Optional[str] = None,
    api_key: Optional[str] = None,
    ranking_profile: str = "dense"
) -> Optional[VespaSearchWrapper]:
    """
    Factory function to create Vespa wrapper with error handling.
    
    Args:
        schema_id: Vespa schema ID
        env: Environment
        gssso_token: Optional GSSSO authentication token
        api_key: Optional API key
        ranking_profile: Ranking profile
        
    Returns:
        VespaSearchWrapper instance or None if unavailable
    """
    try:
        return VespaSearchWrapper(
            schema_id=schema_id,
            env=env,
            gssso_token=gssso_token,
            api_key=api_key,
            ranking_profile=ranking_profile
        )
    except Exception as e:
        print(f"[WARNING] Vespa not available: {e}")
        return None

