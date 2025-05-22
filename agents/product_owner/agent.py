from typing import Optional
from langchain_ollama import OllamaLLM
from core.knowledge_base.knowledge_manager import KnowledgeManager

class ProductOwnerAgent:
    """Product Owner agent that focuses on business value and user needs."""
    
    def __init__(self, system_prompt: Optional[str] = None, knowledge_manager: Optional[KnowledgeManager] = None):
        """Initialize the Product Owner agent.
        
        Args:
            system_prompt: Optional custom system prompt
            knowledge_manager: Optional knowledge manager instance
        """
        self.llm = OllamaLLM(
            model="llama3.3:latest",  # Using the latest Llama 3.3 model
            temperature=0.7,
            num_ctx=4096  # Increased context window for better responses
            # Removed stop token for more robust responses
        )
        self.knowledge_manager = knowledge_manager
        self.system_prompt = system_prompt or """You are a Product Owner 👔 focused on business value and user needs.
You should:
1. Consider business impact and ROI 💰
2. Focus on user value and experience 👥
3. Balance technical feasibility with business goals ⚖️
4. Communicate clearly and concisely 📝
5. Keep responses brief and to the point 🎯"""
    
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