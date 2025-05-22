import logging
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.text import Text
from datetime import datetime
from typing import Optional
from utils.config import settings

# Initialize Rich console
console = Console()

class AgentLogger:
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = logging.getLogger(agent_name)
        self.logger.setLevel(settings.LOG_LEVEL)
        
        # Add Rich handler
        rich_handler = RichHandler(rich_tracebacks=True)
        rich_handler.setFormatter(logging.Formatter(settings.LOG_FORMAT))
        self.logger.addHandler(rich_handler)
    
    def log_communication(self, message: str, to_agent: Optional[str] = None):
        """Log agent communication with rich formatting"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if to_agent:
            title = f"[bold blue]{self.agent_name}[/] → [bold green]{to_agent}[/]"
        else:
            title = f"[bold blue]{self.agent_name}[/]"
        
        panel = Panel(
            Text(message, style="white"),
            title=title,
            subtitle=f"[dim]{timestamp}[/]",
            border_style="blue"
        )
        console.print(panel)
        self.logger.info(f"Communication: {message}")
    
    def log_operation(self, operation: str, details: str):
        """Log file system or API operations"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        panel = Panel(
            Text(details, style="yellow"),
            title=f"[bold red]{operation}[/]",
            subtitle=f"[dim]{timestamp}[/]",
            border_style="red"
        )
        console.print(panel)
        self.logger.info(f"Operation {operation}: {details}")

# Create loggers for both agents
product_owner_logger = AgentLogger("Product Owner")
cto_logger = AgentLogger("CTO") 