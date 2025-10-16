"""
ReAct Agent Implementation using LangGraph
Core agent logic with tool execution and iterative reasoning
"""

from typing import Dict, Any, List, Optional
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage
from llm_adapter import LangChainLLMAdapter
from agent_tools import create_agent_tools
from prompts import AGENT_SYSTEM_PROMPT
from agent_state import AgentState
from kg_retriever import KGRetriever
import json


class DocumentReActAgent:
    """
    ReAct agent for document and knowledge graph analysis.
    Uses LangGraph's create_react_agent for iterative reasoning with tools.
    """
    
    def __init__(
        self,
        llm_adapter: LangChainLLMAdapter,
        kg_retriever: KGRetriever,
        original_documents: str,
        max_iterations: int = 10,
        system_prompt: str = None
    ):
        """
        Initialize the ReAct agent.
        
        Args:
            llm_adapter: LangChain-compatible LLM adapter
            kg_retriever: KGRetriever instance with built knowledge graph
            original_documents: Original document content as string
            max_iterations: Maximum reasoning iterations
            system_prompt: Optional custom system prompt
        """
        self.llm_adapter = llm_adapter
        self.kg_retriever = kg_retriever
        self.original_documents = original_documents
        self.max_iterations = max_iterations
        self.system_prompt = system_prompt or AGENT_SYSTEM_PROMPT
        
        # Create tools
        self.tools = create_agent_tools(kg_retriever, original_documents)
        
        # Create the ReAct agent
        self.agent = create_react_agent(
            model=llm_adapter,
            tools=self.tools,
            state_modifier=self.system_prompt
        )
        
        # State tracking
        self.current_state = None
    
    def run(
        self,
        query: str,
        state: Optional[AgentState] = None,
        include_trace: bool = False
    ) -> Dict[str, Any]:
        """
        Run the agent on a query.
        
        Args:
            query: User query
            state: Optional AgentState for session tracking
            include_trace: Whether to include reasoning trace
            
        Returns:
            Dictionary with response and metadata
        """
        self.current_state = state
        
        try:
            # Prepare messages
            messages = [HumanMessage(content=query)]
            
            # Invoke the agent
            result = self.agent.invoke(
                {"messages": messages},
                config={"recursion_limit": self.max_iterations}
            )
            
            # Extract response and trace
            response_text = self._extract_response(result)
            trace = self._extract_trace(result) if include_trace else None
            
            # Track in state if provided
            if state:
                state.add_to_conversation(query, response_text)
                if trace:
                    state.add_reasoning_path(
                        steps=[step.get('action', '') for step in trace.get('steps', [])],
                        conclusion=response_text
                    )
            
            return {
                'response': response_text,
                'trace': trace,
                'success': True,
                'iterations': len(result.get('messages', [])) // 2,  # Approximate
            }
        
        except Exception as e:
            error_message = f"Agent error: {str(e)}"
            
            if state:
                state.add_to_conversation(query, error_message)
            
            return {
                'response': error_message,
                'trace': None,
                'success': False,
                'error': str(e)
            }
    
    def _extract_response(self, result: Dict[str, Any]) -> str:
        """
        Extract the final response from agent result.
        
        Args:
            result: Agent invocation result
            
        Returns:
            Response text
        """
        try:
            # Get the last message
            messages = result.get('messages', [])
            if messages:
                last_message = messages[-1]
                if hasattr(last_message, 'content'):
                    return str(last_message.content)
                elif isinstance(last_message, dict):
                    return str(last_message.get('content', ''))
            
            return "No response generated"
        
        except Exception as e:
            return f"Error extracting response: {str(e)}"
    
    def _extract_trace(self, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract reasoning trace from agent result.
        
        Args:
            result: Agent invocation result
            
        Returns:
            Trace dictionary or None
        """
        try:
            messages = result.get('messages', [])
            
            trace_steps = []
            for i, msg in enumerate(messages):
                step_info = {
                    'step_number': i + 1,
                    'type': type(msg).__name__,
                }
                
                if hasattr(msg, 'content'):
                    content = str(msg.content)
                    step_info['content'] = content[:500]  # Truncate long content
                    
                    # Try to detect tool calls
                    if 'tool_calls' in dir(msg) and msg.tool_calls:
                        step_info['tool_calls'] = [
                            {
                                'tool': tc.get('name', 'unknown'),
                                'args': tc.get('args', {})
                            }
                            for tc in msg.tool_calls
                        ]
                
                trace_steps.append(step_info)
            
            return {
                'total_steps': len(trace_steps),
                'steps': trace_steps
            }
        
        except Exception as e:
            return {'error': f"Error extracting trace: {str(e)}"}
    
    def stream_run(
        self,
        query: str,
        state: Optional[AgentState] = None
    ):
        """
        Stream agent execution (for real-time updates).
        
        Args:
            query: User query
            state: Optional AgentState
            
        Yields:
            Chunks of the agent's reasoning and response
        """
        self.current_state = state
        
        try:
            messages = [HumanMessage(content=query)]
            
            # Stream the agent execution
            for chunk in self.agent.stream(
                {"messages": messages},
                config={"recursion_limit": self.max_iterations}
            ):
                yield chunk
        
        except Exception as e:
            yield {"error": str(e)}
    
    def get_tool_names(self) -> List[str]:
        """
        Get names of all available tools.
        
        Returns:
            List of tool names
        """
        return [tool.name for tool in self.tools]
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """
        Get descriptions of all tools.
        
        Returns:
            Dictionary mapping tool names to descriptions
        """
        return {
            tool.name: tool.description
            for tool in self.tools
        }


def create_react_agent_instance(
    app_id: str,
    env: str,
    kg_retriever: KGRetriever,
    original_documents: str,
    model_name: str = "gemini-2.0-flash",
    temperature: float = 0.2,
    max_iterations: int = 10,
    log_level: str = "DEBUG"
) -> DocumentReActAgent:
    """
    Factory function to create a configured ReAct agent.
    
    Args:
        app_id: Goldman Sachs app ID
        env: Environment (uat or prod)
        kg_retriever: KGRetriever instance
        original_documents: Original document content
        model_name: LLM model name
        temperature: LLM temperature
        max_iterations: Max reasoning iterations
        log_level: Logging level
        
    Returns:
        Configured DocumentReActAgent instance
    """
    # Create LLM adapter
    llm_adapter = LangChainLLMAdapter(
        app_id=app_id,
        env=env,
        model_name=model_name,
        temperature=temperature,
        log_level=log_level
    )
    
    # Create and return agent
    return DocumentReActAgent(
        llm_adapter=llm_adapter,
        kg_retriever=kg_retriever,
        original_documents=original_documents,
        max_iterations=max_iterations
    )


class AgentOrchestrator:
    """
    High-level orchestrator that manages agent lifecycle and routing.
    """
    
    def __init__(
        self,
        app_id: str,
        env: str,
        model_name: str = "gemini-2.0-flash",
        temperature: float = 0.2
    ):
        """
        Initialize the orchestrator.
        
        Args:
            app_id: App ID
            env: Environment
            model_name: Model name
            temperature: Temperature
        """
        self.app_id = app_id
        self.env = env
        self.model_name = model_name
        self.temperature = temperature
        self.agent = None
        self.kg_retriever = None
    
    def initialize(self, kg_retriever: KGRetriever, original_documents: str):
        """
        Initialize the agent with KG and documents.
        
        Args:
            kg_retriever: KGRetriever instance
            original_documents: Document content
        """
        self.kg_retriever = kg_retriever
        
        self.agent = create_react_agent_instance(
            app_id=self.app_id,
            env=self.env,
            kg_retriever=kg_retriever,
            original_documents=original_documents,
            model_name=self.model_name,
            temperature=self.temperature
        )
    
    def query(
        self,
        query: str,
        include_trace: bool = False,
        state: Optional[AgentState] = None
    ) -> Dict[str, Any]:
        """
        Query the agent.
        
        Args:
            query: User query
            include_trace: Include reasoning trace
            state: Optional state
            
        Returns:
            Response dictionary
        """
        if not self.agent:
            return {
                'response': 'Agent not initialized. Please process documents first.',
                'success': False
            }
        
        return self.agent.run(query, state=state, include_trace=include_trace)
    
    def is_initialized(self) -> bool:
        """Check if agent is initialized."""
        return self.agent is not None

