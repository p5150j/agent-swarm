import typer
from rich.console import Console
from rich.prompt import Prompt
from agents.product_owner.agent import ProductOwnerAgent
from agents.cto.agent import CTOAgent
from utils.config import settings

app = typer.Typer()
console = Console()

class AgentCollaboration:
    def __init__(self):
        self.product_owner = ProductOwnerAgent()
        self.cto = CTOAgent()
        self.max_iterations = 10  # Prevent infinite loops
    
    def start_collaboration(self, initial_prompt: str):
        console.print("\n[bold green]Starting Agent Collaboration[/bold green]")
        console.print(f"[bold]Initial Prompt:[/bold] {initial_prompt}\n")
        
        # Start with Product Owner's perspective
        current_agent = self.product_owner
        other_agent = self.cto
        message = initial_prompt
        iteration = 0
        
        while iteration < self.max_iterations:
            # Get response from current agent
            response = current_agent.process_message(message, from_agent=other_agent.name)
            
            # Check if we've reached a conclusion
            if self._is_conclusion(response):
                console.print("\n[bold green]Collaboration Complete![/bold green]")
                console.print(f"[bold]Final Solution:[/bold]\n{response}")
                break
            
            # Switch agents
            current_agent, other_agent = other_agent, current_agent
            message = response
            iteration += 1
        
        if iteration >= self.max_iterations:
            console.print("\n[bold yellow]Maximum iterations reached. Collaboration ended.[/bold yellow]")
    
    def _is_conclusion(self, response: str) -> bool:
        """Check if the response indicates a conclusion has been reached"""
        # TODO: Implement more sophisticated conclusion detection
        conclusion_indicators = [
            "final solution",
            "conclusion",
            "agreed upon",
            "consensus reached",
            "best approach"
        ]
        return any(indicator in response.lower() for indicator in conclusion_indicators)

@app.command()
def collaborate(
    prompt: str = typer.Option(..., prompt=True, help="The initial prompt for the agents to collaborate on")
):
    """Start a collaboration between the Product Owner and CTO agents."""
    collaboration = AgentCollaboration()
    collaboration.start_collaboration(prompt)

if __name__ == "__main__":
    app() 