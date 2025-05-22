from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from langchain_ollama import ChatOllama
from langchain_community.chat_models import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from utils.config import settings
from core.logging import AgentLogger

class BaseAgent(ABC):
    def __init__(self, name: str, knowledge_base_path: str):
        self.name = name
        self.knowledge_base_path = knowledge_base_path
        self.logger = AgentLogger(name)
        
        # Initialize LLM
        if settings.LLM_PROVIDER == "ollama":
            self.llm = ChatOllama(
                base_url=settings.OLLAMA_API_URL,
                model=settings.MODEL_NAME
            )
        else:
            self.llm = ChatAnthropic(
                anthropic_api_key=settings.ANTHROPIC_API_KEY,
                model_name=settings.MODEL_NAME
            )
        
        # Initialize conversation chain
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "{system_prompt}"),
            ("human", "{input}")
        ])
        
        self.chain = (
            {"system_prompt": lambda x: self.get_system_prompt(), "input": RunnablePassthrough()}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        
        # Load agent's knowledge base
        self.knowledge_base = self._load_knowledge_base()
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load agent's knowledge base from files"""
        # TODO: Implement knowledge base loading from files
        return {}
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt that defines the agent's persona"""
        pass
    
    def process_message(self, message: str, from_agent: Optional[str] = None) -> str:
        """Process incoming message and generate response"""
        # Log incoming message
        if from_agent:
            self.logger.log_communication(f"Received from {from_agent}: {message}")
        
        # Create the prompt with context
        if from_agent:
            prompt = f"""As the {self.name}, you are responding to a message from the {from_agent}. 
            Your role is to provide your unique perspective and expertise.

            Original message from {from_agent}:
            {message}

            IMPORTANT: Do not repeat or echo the message above. Instead, provide your own analysis and recommendations.
            Focus on your specific role and expertise. For example:
            - If you are the CTO, provide technical implementation details, architecture considerations, and specific technology recommendations
            - If you are the Product Owner, focus on user needs, business value, and product strategy

            Your response should be original and reflect your unique perspective."""
        else:
            prompt = message
        
        # Get response from LLM
        response = self.chain.invoke(prompt)
        
        # Log response
        self.logger.log_communication(response)
        
        return response
    
    def perform_operation(self, operation: str, details: str):
        """Log and perform an operation (file system, API, etc.)"""
        self.logger.log_operation(operation, details)
        # TODO: Implement actual operation execution
    
    def get_knowledge(self, query: str) -> str:
        """Query the agent's knowledge base"""
        # TODO: Implement knowledge base querying
        return "" 