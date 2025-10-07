"""
LLM Handler Module
Manages LLM interactions for document querying
"""

from goldmansachs.awm_genai import LLM, LLMConfig
from typing import List, Dict, Any, Optional


class LLMHandler:
    """Handles LLM initialization and inference."""
    
    def __init__(
        self,
        app_id: str,
        env: str,
        model_name: str = "gemini-2.0-flash",
        temperature: float = 0,
        log_level: str = "DEBUG"
    ):
        """
        Initialize LLM Handler.
        
        Args:
            app_id: Application ID
            env: Environment (uat or prod)
            model_name: Name of the model to use
            temperature: Temperature for generation (0-1)
            log_level: Logging level
        """
        self.app_id = app_id
        self.env = env
        self.model_name = model_name
        self.temperature = temperature
        self.log_level = log_level
        
        # Initialize LLM configuration
        self.config = LLMConfig(
            app_id=app_id,
            env=env,
            model_name=model_name,
            temperature=temperature,
            log_level=log_level,
        )
        
        # Initialize LLM
        self.llm = LLM.init(config=self.config)
    
    def query(
        self,
        question: str,
        documents: List[Any],
        context: Optional[str] = None
    ) -> str:
        """
        Query the LLM with documents.
        
        Args:
            question: Question to ask
            documents: List of document objects
            context: Optional context to include
            
        Returns:
            LLM response
        """
        # Build the query
        if context:
            full_question = f"{context}\n\n{question}"
        else:
            full_question = question
        
        # Invoke LLM
        response = self.llm.invoke(
            full_question,
            documents=documents,
        )
        
        return response
    
    def batch_query(
        self,
        questions: List[str],
        documents: List[Any]
    ) -> List[Dict[str, str]]:
        """
        Process multiple questions.
        
        Args:
            questions: List of questions
            documents: List of document objects
            
        Returns:
            List of question-response pairs
        """
        results = []
        
        for question in questions:
            response = self.query(question, documents)
            results.append({
                "question": question,
                "response": response
            })
        
        return results

