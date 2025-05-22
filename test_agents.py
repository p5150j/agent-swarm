import typer
from rich.console import Console
from rich.panel import Panel
from agents.product_owner.agent import ProductOwnerAgent
from agents.cto.agent import CTOAgent
from utils.config import settings
from core.knowledge_base.knowledge_manager import KnowledgeManager
from pathlib import Path

app = typer.Typer()
console = Console()

def get_agent_system_prompt(agent_name: str) -> str:
    """Generate a system prompt for an agent using their knowledge base."""
    # Initialize the knowledge manager
    manager = KnowledgeManager(agent_name)
    
    # Load the role definition
    role_file = Path(f"agents/{agent_name}/knowledge_base/documents/role.md")
    if role_file.exists():
        role_doc = manager.load_document(role_file, "markdown")
        
        # Create the system prompt
        prompt = f"""You are an AI agent acting as a {agent_name.replace('_', ' ').title()}.
Your role and responsibilities are defined in the following knowledge base:

{role_doc.content}

You should:
1. Always act according to your defined role and responsibilities
2. Make decisions based on your decision-making framework
3. Communicate in your specified style
4. Focus on your key areas of expertise

When responding to queries or making decisions, always consider your role and expertise."""
        
        return prompt
    else:
        raise FileNotFoundError(f"Role definition not found for {agent_name}")

def test_ollama_connection():
    """Test if Ollama is running and accessible"""
    try:
        import requests
        response = requests.get(settings.OLLAMA_API_URL)
        if response.status_code == 200:
            console.print("[green]✓ Ollama is running and accessible[/green]")
            return True
        else:
            console.print(f"[red]✗ Ollama returned status code: {response.status_code}[/red]")
            return False
    except requests.exceptions.ConnectionError:
        console.print("[red]✗ Could not connect to Ollama. Is it running?[/red]")
        return False

def test_agent_communication():
    """Test basic communication between agents"""
    console.print("\n[bold blue]Testing Agent Communication[/bold blue]")
    
    # Initialize knowledge managers
    po_knowledge = KnowledgeManager("product_owner")
    cto_knowledge = KnowledgeManager("cto")
    
    # Get system prompts with knowledge base
    po_prompt = get_agent_system_prompt("product_owner")
    cto_prompt = get_agent_system_prompt("cto")
    
    # Initialize agents with their knowledge
    po = ProductOwnerAgent(system_prompt=po_prompt, knowledge_manager=po_knowledge)
    cto = CTOAgent(system_prompt=cto_prompt, knowledge_manager=cto_knowledge)
    
    # Test cases
    test_cases = [
        {
            "name": "Data Export Feature",
            "prompt": "We need to implement a new feature that allows users to export their data in multiple formats (CSV, JSON, Excel). What are your thoughts?"
        },
        {
            "name": "Real-time Analytics",
            "prompt": "Users want to see real-time analytics of their data with interactive charts and graphs. How can we implement this?"
        }
    ]
    
    for test_case in test_cases:
        console.print(f"\n[bold cyan]Test Case: {test_case['name']}[/bold cyan]")
        console.print(f"[bold]Initial Prompt:[/bold] {test_case['prompt']}\n")
        
        # Get Product Owner's perspective
        po_response = po.process_message(test_case['prompt'])
        console.print(Panel(po_response, title="[bold green]Product Owner Response[/bold green]"))
        
        # Get CTO's response to Product Owner
        cto_response = cto.process_message(po_response, from_agent="Product Owner")
        console.print(Panel(cto_response, title="[bold blue]CTO Response[/bold blue]"))
        
        # Get Product Owner's final thoughts
        final_response = po.process_message(cto_response, from_agent="CTO")
        console.print(Panel(final_response, title="[bold green]Product Owner Final Thoughts[/bold green]"))
        
        console.print("\n" + "="*80 + "\n")

@app.command()
def test():
    """Run tests to verify LLM setup and agent communication"""
    console.print("[bold]Starting Agent System Tests[/bold]\n")
    
    # Test Ollama connection
    if not test_ollama_connection():
        console.print("\n[yellow]Please make sure Ollama is installed and running:[/yellow]")
        console.print("1. Install Ollama from https://ollama.ai")
        console.print("2. Run 'ollama serve' in a terminal")
        console.print("3. Run 'ollama pull llama2:13b' to download the model")
        return
    
    # Test agent communication
    test_agent_communication()

if __name__ == "__main__":
    app() 