"""
Query Router for Intelligent Routing Between Simple and Agent Flows
Analyzes query complexity to determine the best processing approach
"""

import re
from typing import Dict, Any, Tuple


class QueryRouter:
    """
    Routes queries to either simple KG retrieval or ReAct agent based on complexity.
    """
    
    def __init__(self, complexity_threshold: int = 60):
        """
        Initialize the query router.
        
        Args:
            complexity_threshold: Threshold score (0-100) above which to use agent
        """
        self.complexity_threshold = complexity_threshold
        
        # Patterns indicating complex queries
        self.complex_patterns = {
            'multi_hop': [
                r'how.*relate',
                r'connect.*to',
                r'relationship between',
                r'link.*to',
                r'associate.*with',
            ],
            'impact_analysis': [
                r'what would.*affect',
                r'impact.*of',
                r'if.*remove',
                r'consequence',
                r'downstream',
                r'depend.*on',
            ],
            'gap_analysis': [
                r'what.*missing',
                r'which.*lack',
                r'don\'t have',
                r'without',
                r'gap',
                r'coverage',
            ],
            'comparative': [
                r'compare',
                r'difference between',
                r'versus',
                r'vs',
                r'both.*and',
                r'either.*or',
            ],
            'complex_aggregation': [
                r'all.*that.*and',
                r'comprehensive',
                r'everything.*about',
                r'complete.*analysis',
            ],
        }
        
        # Patterns indicating simple queries
        self.simple_patterns = {
            'single_entity': [
                r'^what is\s+\w+[\-\d]*\s*\?*$',
                r'^define\s+\w+',
                r'^explain\s+\w+[\-\d]*\s*\?*$',
            ],
            'simple_list': [
                r'^list all\s+\w+s*\s*\?*$',
                r'^show me all\s+\w+s*\s*\?*$',
                r'^get all\s+\w+s*\s*\?*$',
            ],
        }
    
    def calculate_complexity_score(self, query: str) -> int:
        """
        Calculate a complexity score for the query.
        
        Args:
            query: User query
            
        Returns:
            Complexity score (0-100)
        """
        score = 0
        query_lower = query.lower()
        
        # Base score from query length
        word_count = len(query.split())
        if word_count > 15:
            score += 20
        elif word_count > 10:
            score += 10
        elif word_count > 5:
            score += 5
        
        # Check for complex pattern matches
        for category, patterns in self.complex_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    if category == 'multi_hop':
                        score += 30
                    elif category == 'impact_analysis':
                        score += 35
                    elif category == 'gap_analysis':
                        score += 25
                    elif category == 'comparative':
                        score += 30
                    elif category == 'complex_aggregation':
                        score += 20
                    break  # Only count once per category
        
        # Check for simple pattern matches (reduce score)
        for category, patterns in self.simple_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    score -= 20
                    break
        
        # Check for multiple entities mentioned
        entity_indicators = [
            r'\b[A-Z]{2,}-\d+',  # Control IDs like AC-2
            r'\bR-\d+',  # Risk IDs
            r'\bREQ-\d+',  # Requirement IDs
            r'\bISO\s+\d+',  # Standards
            r'\bNIST',
        ]
        entity_count = 0
        for pattern in entity_indicators:
            entity_count += len(re.findall(pattern, query))
        
        if entity_count > 2:
            score += 25
        elif entity_count == 2:
            score += 15
        
        # Check for question complexity indicators
        complexity_words = [
            'analyze', 'evaluate', 'assess', 'determine',
            'comprehensive', 'detailed', 'thorough',
            'all', 'every', 'each'
        ]
        complexity_count = sum(1 for word in complexity_words if word in query_lower)
        score += complexity_count * 5
        
        # Check for multiple questions
        question_marks = query.count('?')
        if question_marks > 1:
            score += 15
        
        # Presence of logical operators
        if re.search(r'\b(and|or|but|however|also)\b', query_lower):
            score += 10
        
        # Cap at 100
        return min(100, max(0, score))
    
    def detect_query_type(self, query: str) -> str:
        """
        Detect the type of query.
        
        Args:
            query: User query
            
        Returns:
            Query type string
        """
        query_lower = query.lower()
        
        # Check complex patterns first
        for category, patterns in self.complex_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return category
        
        # Check simple patterns
        for category, patterns in self.simple_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return category
        
        # Detect by keywords
        if any(word in query_lower for word in ['list', 'show', 'all']):
            return 'list'
        elif any(word in query_lower for word in ['what is', 'define', 'explain']):
            return 'explain'
        elif any(word in query_lower for word in ['how', 'why']):
            return 'complex_reasoning'
        
        return 'general'
    
    def should_use_agent(self, query: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Determine if the query should use the ReAct agent.
        
        Args:
            query: User query
            
        Returns:
            Tuple of (use_agent: bool, analysis: dict)
        """
        complexity_score = self.calculate_complexity_score(query)
        query_type = self.detect_query_type(query)
        
        # Determine if agent should be used
        use_agent = complexity_score >= self.complexity_threshold
        
        # Force agent for certain query types
        force_agent_types = [
            'multi_hop',
            'impact_analysis',
            'gap_analysis',
            'comparative',
            'complex_aggregation'
        ]
        
        if query_type in force_agent_types:
            use_agent = True
        
        # Force simple flow for certain types
        force_simple_types = ['single_entity', 'simple_list']
        if query_type in force_simple_types and complexity_score < 40:
            use_agent = False
        
        analysis = {
            'complexity_score': complexity_score,
            'query_type': query_type,
            'use_agent': use_agent,
            'routing_reason': self._get_routing_reason(
                use_agent,
                complexity_score,
                query_type
            ),
            'query_length': len(query.split())
        }
        
        return use_agent, analysis
    
    def _get_routing_reason(
        self,
        use_agent: bool,
        complexity_score: int,
        query_type: str
    ) -> str:
        """
        Generate a human-readable reason for the routing decision.
        
        Args:
            use_agent: Whether agent was selected
            complexity_score: Calculated complexity score
            query_type: Detected query type
            
        Returns:
            Reason string
        """
        if use_agent:
            if query_type in ['multi_hop', 'impact_analysis', 'gap_analysis']:
                return f"Complex query type '{query_type}' requires multi-step reasoning"
            elif complexity_score >= 80:
                return f"Very high complexity (score: {complexity_score}) requires agent capabilities"
            elif complexity_score >= self.complexity_threshold:
                return f"Complexity score {complexity_score} exceeds threshold {self.complexity_threshold}"
            else:
                return "Query requires advanced reasoning capabilities"
        else:
            if query_type in ['single_entity', 'simple_list']:
                return f"Simple '{query_type}' query can be handled with direct retrieval"
            elif complexity_score < 40:
                return f"Low complexity (score: {complexity_score}) suitable for simple flow"
            else:
                return "Query can be handled efficiently with direct KG retrieval"
    
    def get_routing_statistics(self, queries: list) -> Dict[str, Any]:
        """
        Analyze a batch of queries and provide routing statistics.
        
        Args:
            queries: List of query strings
            
        Returns:
            Statistics dictionary
        """
        agent_count = 0
        simple_count = 0
        complexity_scores = []
        query_types = {}
        
        for query in queries:
            use_agent, analysis = self.should_use_agent(query)
            
            if use_agent:
                agent_count += 1
            else:
                simple_count += 1
            
            complexity_scores.append(analysis['complexity_score'])
            
            query_type = analysis['query_type']
            query_types[query_type] = query_types.get(query_type, 0) + 1
        
        return {
            'total_queries': len(queries),
            'agent_routed': agent_count,
            'simple_routed': simple_count,
            'agent_percentage': (agent_count / len(queries) * 100) if queries else 0,
            'avg_complexity': sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0,
            'query_type_distribution': query_types,
        }


# Convenience function
def route_query(
    query: str,
    complexity_threshold: int = 60
) -> Tuple[bool, Dict[str, Any]]:
    """
    Route a single query.
    
    Args:
        query: User query
        complexity_threshold: Threshold for using agent
        
    Returns:
        Tuple of (use_agent, analysis)
    """
    router = QueryRouter(complexity_threshold=complexity_threshold)
    return router.should_use_agent(query)

