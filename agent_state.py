"""
Agent State and Memory Management
Manages conversation state, memory, and context for multi-turn interactions
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict
import json


class AgentState:
    """
    Maintains state for a single agent conversation session.
    Tracks discovered entities, reasoning paths, and conversation history.
    """
    
    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize agent state.
        
        Args:
            session_id: Optional session identifier
        """
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.created_at = datetime.now()
        
        # Entity tracking
        self.discovered_entities = {}  # entity_id -> entity_data
        self.entity_access_count = defaultdict(int)  # entity_id -> count
        
        # Relationship tracking
        self.explored_relationships = []  # List of (source, target, rel_type)
        
        # Tool usage tracking
        self.tool_calls = []  # List of tool call records
        self.tool_usage_count = defaultdict(int)  # tool_name -> count
        
        # Conversation history
        self.conversation_history = []  # List of {query, response, timestamp}
        
        # Reasoning paths
        self.reasoning_paths = []  # List of reasoning chains
        
        # Current context
        self.current_context = {
            'active_entities': set(),  # Currently relevant entity IDs
            'active_topics': set(),  # Current topics
        }
    
    def add_discovered_entity(self, entity_id: str, entity_data: Dict[str, Any]):
        """
        Add a discovered entity to state.
        
        Args:
            entity_id: Entity identifier
            entity_data: Entity information
        """
        if entity_id not in self.discovered_entities:
            self.discovered_entities[entity_id] = {
                **entity_data,
                'discovered_at': datetime.now().isoformat(),
                'access_count': 0
            }
        
        self.entity_access_count[entity_id] += 1
        self.discovered_entities[entity_id]['access_count'] = self.entity_access_count[entity_id]
        
        # Add to active entities
        self.current_context['active_entities'].add(entity_id)
    
    def add_relationship(self, source_id: str, target_id: str, rel_type: str):
        """
        Record an explored relationship.
        
        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            rel_type: Relationship type
        """
        relationship = (source_id, target_id, rel_type)
        if relationship not in self.explored_relationships:
            self.explored_relationships.append(relationship)
    
    def record_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Any,
        success: bool = True
    ):
        """
        Record a tool call.
        
        Args:
            tool_name: Name of the tool called
            arguments: Arguments passed to the tool
            result: Tool result
            success: Whether the call was successful
        """
        self.tool_calls.append({
            'tool': tool_name,
            'arguments': arguments,
            'result': str(result)[:500],  # Truncate long results
            'success': success,
            'timestamp': datetime.now().isoformat()
        })
        
        self.tool_usage_count[tool_name] += 1
    
    def add_to_conversation(self, query: str, response: str, metadata: Dict[str, Any] = None):
        """
        Add a conversation turn to history.
        
        Args:
            query: User query
            response: Agent response
            metadata: Optional metadata about the turn
        """
        self.conversation_history.append({
            'query': query,
            'response': response,
            'metadata': metadata or {},
            'timestamp': datetime.now().isoformat()
        })
    
    def add_reasoning_path(self, steps: List[str], conclusion: str):
        """
        Record a reasoning path.
        
        Args:
            steps: List of reasoning steps
            conclusion: Final conclusion
        """
        self.reasoning_paths.append({
            'steps': steps,
            'conclusion': conclusion,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_relevant_context(self, top_k: int = 5) -> Dict[str, Any]:
        """
        Get the most relevant context for the current conversation.
        
        Args:
            top_k: Number of top entities to include
            
        Returns:
            Context dictionary
        """
        # Get most frequently accessed entities
        top_entities = sorted(
            self.entity_access_count.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]
        
        return {
            'recent_entities': [eid for eid, _ in top_entities],
            'active_entities': list(self.current_context['active_entities']),
            'recent_topics': list(self.current_context['active_topics']),
            'conversation_turns': len(self.conversation_history),
            'tools_used': list(self.tool_usage_count.keys())
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the session.
        
        Returns:
            Statistics dictionary
        """
        return {
            'session_id': self.session_id,
            'session_duration': (datetime.now() - self.created_at).total_seconds(),
            'conversation_turns': len(self.conversation_history),
            'entities_discovered': len(self.discovered_entities),
            'relationships_explored': len(self.explored_relationships),
            'tool_calls_made': len(self.tool_calls),
            'tool_usage': dict(self.tool_usage_count),
            'most_accessed_entities': sorted(
                self.entity_access_count.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
    
    def clear_context(self):
        """Clear the current context (for topic switches)."""
        self.current_context = {
            'active_entities': set(),
            'active_topics': set(),
        }
    
    def export_state(self) -> str:
        """
        Export state as JSON string.
        
        Returns:
            JSON string of state
        """
        return json.dumps({
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'statistics': self.get_statistics(),
            'discovered_entities': {
                eid: {
                    **edata,
                    'last_accessed': datetime.now().isoformat()
                }
                for eid, edata in list(self.discovered_entities.items())[:20]
            },
            'recent_tools': list(self.tool_usage_count.keys()),
        }, indent=2)


class AgentMemory:
    """
    Manages memory across multiple sessions.
    Can persist and retrieve state for conversation continuity.
    """
    
    def __init__(self):
        """Initialize agent memory."""
        self.sessions = {}  # session_id -> AgentState
        self.current_session_id = None
    
    def create_session(self, session_id: Optional[str] = None) -> AgentState:
        """
        Create a new session.
        
        Args:
            session_id: Optional session ID
            
        Returns:
            New AgentState instance
        """
        state = AgentState(session_id=session_id)
        self.sessions[state.session_id] = state
        self.current_session_id = state.session_id
        return state
    
    def get_session(self, session_id: str) -> Optional[AgentState]:
        """
        Get a session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            AgentState if found, None otherwise
        """
        return self.sessions.get(session_id)
    
    def get_current_session(self) -> Optional[AgentState]:
        """
        Get the current active session.
        
        Returns:
            Current AgentState if exists
        """
        if self.current_session_id:
            return self.sessions.get(self.current_session_id)
        return None
    
    def set_current_session(self, session_id: str):
        """
        Set the current active session.
        
        Args:
            session_id: Session to make current
        """
        if session_id in self.sessions:
            self.current_session_id = session_id
    
    def delete_session(self, session_id: str):
        """
        Delete a session.
        
        Args:
            session_id: Session to delete
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            if self.current_session_id == session_id:
                self.current_session_id = None
    
    def get_all_sessions(self) -> List[str]:
        """
        Get all session IDs.
        
        Returns:
            List of session IDs
        """
        return list(self.sessions.keys())
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """
        Get statistics across all sessions.
        
        Returns:
            Memory statistics
        """
        total_turns = sum(
            len(state.conversation_history)
            for state in self.sessions.values()
        )
        
        total_entities = sum(
            len(state.discovered_entities)
            for state in self.sessions.values()
        )
        
        total_tools = sum(
            len(state.tool_calls)
            for state in self.sessions.values()
        )
        
        return {
            'total_sessions': len(self.sessions),
            'active_session': self.current_session_id,
            'total_conversation_turns': total_turns,
            'total_entities_discovered': total_entities,
            'total_tool_calls': total_tools,
        }


# Global memory instance (can be used across the application)
_global_memory = None


def get_global_memory() -> AgentMemory:
    """
    Get the global agent memory instance.
    
    Returns:
        Global AgentMemory instance
    """
    global _global_memory
    if _global_memory is None:
        _global_memory = AgentMemory()
    return _global_memory


def create_session_state(session_id: Optional[str] = None) -> AgentState:
    """
    Convenience function to create a new session state.
    
    Args:
        session_id: Optional session ID
        
    Returns:
        New AgentState instance
    """
    memory = get_global_memory()
    return memory.create_session(session_id)

