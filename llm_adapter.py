"""
LLM Adapter for LangChain Integration
Wraps goldmansachs.awm_genai.LLM to be compatible with LangChain's BaseChatModel
"""

from typing import Any, List, Optional, Iterator, Dict
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from goldmansachs.awm_genai import LLM, LLMConfig
import json


class LangChainLLMAdapter(BaseChatModel):
    """
    Adapter to make goldmansachs.awm_genai.LLM compatible with LangChain.
    
    This adapter allows the Goldman Sachs LLM to be used with LangChain agents
    and chains while preserving all existing configuration.
    """
    
    app_id: str
    env: str
    model_name: str = "gemini-2.0-flash"
    temperature: float = 0.0
    log_level: str = "DEBUG"
    _llm: Any = None
    
    def __init__(
        self,
        app_id: str,
        env: str,
        model_name: str = "gemini-2.0-flash",
        temperature: float = 0.0,
        log_level: str = "DEBUG",
        **kwargs
    ):
        """Initialize the LLM adapter."""
        super().__init__(**kwargs)
        self.app_id = app_id
        self.env = env
        self.model_name = model_name
        self.temperature = temperature
        self.log_level = log_level
        
        # Initialize the Goldman Sachs LLM
        config = LLMConfig(
            app_id=app_id,
            env=env,
            model_name=model_name,
            temperature=temperature,
            log_level=log_level,
        )
        self._llm = LLM.init(config=config)
    
    @property
    def _llm_type(self) -> str:
        """Return type of LLM."""
        return "goldmansachs-awm-genai"
    
    def _convert_messages_to_prompt(self, messages: List[BaseMessage]) -> str:
        """
        Convert LangChain messages to a prompt string.
        
        Args:
            messages: List of LangChain messages
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = []
        
        for message in messages:
            if isinstance(message, SystemMessage):
                prompt_parts.append(f"System: {message.content}")
            elif isinstance(message, HumanMessage):
                prompt_parts.append(f"Human: {message.content}")
            elif isinstance(message, AIMessage):
                prompt_parts.append(f"Assistant: {message.content}")
            else:
                # Generic message
                prompt_parts.append(str(message.content))
        
        return "\n\n".join(prompt_parts)
    
    def _extract_response_content(self, response: Any) -> str:
        """
        Extract text content from Goldman Sachs LLM response.
        
        Args:
            response: Raw response from GS LLM
            
        Returns:
            Extracted text content
        """
        # Try different response formats
        try:
            # Method 1: Check for content attribute
            if hasattr(response, 'content'):
                return str(response.content)
            
            # Method 2: Check if it's a dict with Response.content
            elif isinstance(response, dict):
                if 'Response' in response and isinstance(response['Response'], dict):
                    return str(response['Response'].get('content', ''))
                elif 'content' in response:
                    return str(response['content'])
                else:
                    # Try to find any key that might contain the answer
                    for key in ['answer', 'text', 'message', 'result']:
                        if key in response:
                            return str(response[key])
            
            # Method 3: It's already a string
            elif isinstance(response, str):
                return response
            
            # Fallback: convert to string
            return str(response)
            
        except Exception as e:
            return f"[Error extracting response: {str(e)}]"
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        Generate a response from the LLM.
        
        Args:
            messages: List of messages to send to the LLM
            stop: Optional list of stop sequences
            run_manager: Optional callback manager
            **kwargs: Additional arguments
            
        Returns:
            ChatResult with the LLM response
        """
        # Convert messages to prompt
        prompt = self._convert_messages_to_prompt(messages)
        
        # Invoke the Goldman Sachs LLM
        try:
            response = self._llm.invoke(prompt)
            response_text = self._extract_response_content(response)
            
            # Clean up escape sequences
            response_text = response_text.replace('\\n\\n', '\n\n')
            response_text = response_text.replace('\\n', '\n')
            response_text = response_text.replace('\\t', '\t')
            response_text = response_text.strip()
            
        except Exception as e:
            response_text = f"[Error generating response: {str(e)}]"
        
        # Create ChatGeneration
        generation = ChatGeneration(message=AIMessage(content=response_text))
        
        return ChatResult(generations=[generation])
    
    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGeneration]:
        """
        Stream responses from the LLM.
        
        Note: The Goldman Sachs LLM may not support streaming, so this
        falls back to non-streaming generation.
        
        Args:
            messages: List of messages
            stop: Optional stop sequences
            run_manager: Optional callback manager
            **kwargs: Additional arguments
            
        Yields:
            ChatGeneration chunks
        """
        # Fallback to non-streaming
        result = self._generate(messages, stop, run_manager, **kwargs)
        yield result.generations[0]
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Get the identifying parameters."""
        return {
            "app_id": self.app_id,
            "env": self.env,
            "model_name": self.model_name,
            "temperature": self.temperature,
        }
    
    def bind_tools(self, tools: List[Any], **kwargs: Any) -> "LangChainLLMAdapter":
        """
        Bind tools to the LLM for function calling.
        
        Note: This is a placeholder. Tool binding will be handled by
        LangGraph's create_react_agent.
        
        Args:
            tools: List of tools to bind
            **kwargs: Additional arguments
            
        Returns:
            Self for chaining
        """
        # LangGraph will handle tool calling via the ReAct pattern
        return self


def create_llm_adapter(
    app_id: str,
    env: str,
    model_name: str = "gemini-2.0-flash",
    temperature: float = 0.0,
    log_level: str = "DEBUG"
) -> LangChainLLMAdapter:
    """
    Factory function to create an LLM adapter.
    
    Args:
        app_id: Goldman Sachs app ID
        env: Environment (uat or prod)
        model_name: Model name to use
        temperature: Temperature for generation
        log_level: Logging level
        
    Returns:
        Configured LangChainLLMAdapter instance
    """
    return LangChainLLMAdapter(
        app_id=app_id,
        env=env,
        model_name=model_name,
        temperature=temperature,
        log_level=log_level
    )

