from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path

class Settings(BaseSettings):
    # LLM Configuration
    LLM_PROVIDER: str = "ollama"  # or "claude"
    OLLAMA_API_URL: str = "http://localhost:11434"
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # Model Configuration
    MODEL_NAME: str = "llama2:13b"  # Using the 13B parameter model for better quality
    
    # Project Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    PRODUCT_OWNER_KB: Path = BASE_DIR / "agents" / "product_owner" / "knowledge_base"
    CTO_KB: Path = BASE_DIR / "agents" / "cto" / "knowledge_base"
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 