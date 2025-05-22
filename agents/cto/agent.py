from typing import Optional
from langchain_ollama import OllamaLLM
from core.knowledge_base.knowledge_manager import KnowledgeManager

class CTOAgent:
    """CTO agent that focuses on technical excellence and system architecture."""
    
    def __init__(self, system_prompt: Optional[str] = None, knowledge_manager: Optional[KnowledgeManager] = None):
        """Initialize the CTO agent.
        
        Args:
            system_prompt: Optional custom system prompt
            knowledge_manager: Optional knowledge manager instance
        """
        self.llm = OllamaLLM(
            model="llama3.3:latest",  # Using the latest Llama 3.3 model
            temperature=0.7,
            num_ctx=4096,  # Increased context window for better responses
            # Removed stop token for more robust responses
        )
        self.knowledge_manager = knowledge_manager
        self.system_prompt = system_prompt or """You are a CTO 🎮 focused on technical excellence and system architecture.
You should:
1. Consider technical feasibility and scalability 🚀
2. Focus on system architecture and security 🔒
3. Balance technical debt with business needs ⚖️
4. Communicate technical concepts clearly 📊
5. Keep responses detailed and comprehensive 📝"""
    
    def process_message(self, message: str, from_agent: Optional[str] = None) -> str:
        """Process a message and generate a response.
        
        Args:
            message: The message to process
            from_agent: Optional name of the agent who sent the message
            
        Returns:
            The agent's response
        """
        # Query knowledge base if available
        relevant_docs = []
        if self.knowledge_manager:
            relevant_docs = self.knowledge_manager.query_knowledge(message)
        
        # Build the prompt
        prompt = f"{self.system_prompt}\n\n"
        
        if from_agent:
            prompt += f"Message from {from_agent}:\n{message}\n\n"
        else:
            prompt += f"User request:\n{message}\n\n"
        
        if relevant_docs:
            prompt += "Relevant knowledge from your knowledge base:\n"
            for doc in relevant_docs:
                prompt += f"- {doc.content}\n"
            prompt += "\n"
        
        prompt += "Please provide a detailed, thoughtful response based on your role, the knowledge provided, and the previous agent's reasoning. Build on their points, add your own insights, and use diagrams or pseudocode as appropriate."
        
        # Generate response
        response = self.llm.invoke(prompt)
        return response.strip() 