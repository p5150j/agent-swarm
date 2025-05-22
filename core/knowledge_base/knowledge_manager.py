from pathlib import Path
from typing import Dict, List, Optional, Union
import json
import logging
from pydantic import BaseModel, Field
from PyPDF2 import PdfReader
import pandas as pd

logger = logging.getLogger(__name__)

class Document(BaseModel):
    """Represents a document in the knowledge base."""
    content: str
    metadata: Dict = Field(default_factory=dict)
    source: str
    doc_type: str

class KnowledgeManager:
    """Manages the knowledge base for an agent."""
    
    def __init__(self, agent_name: str, base_path: Optional[Path] = None):
        """Initialize the knowledge manager for an agent.
        
        Args:
            agent_name: Name of the agent (e.g., 'product_owner', 'cto')
            base_path: Optional custom path for the knowledge base
        """
        self.agent_name = agent_name
        self.base_path = base_path or Path(f"agents/{agent_name}/knowledge_base")
        self.documents: Dict[str, Document] = {}
        self._ensure_directory_structure()
        
    def _ensure_directory_structure(self) -> None:
        """Ensure the knowledge base directory structure exists."""
        self.base_path.mkdir(parents=True, exist_ok=True)
        (self.base_path / "documents").mkdir(exist_ok=True)
        (self.base_path / "processed").mkdir(exist_ok=True)
        
    def load_document(self, file_path: Union[str, Path], doc_type: str = "text") -> Document:
        """Load a document into the knowledge base.
        
        Args:
            file_path: Path to the document
            doc_type: Type of document ('pdf', 'markdown', 'spreadsheet', 'text')
            
        Returns:
            Document object containing the processed content
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")
            
        try:
            if doc_type == "pdf":
                content = self._process_pdf(file_path)
            elif doc_type == "spreadsheet":
                content = self._process_spreadsheet(file_path)
            elif doc_type == "markdown":
                content = self._process_markdown(file_path)
            else:
                content = self._process_text(file_path)
                
            document = Document(
                content=content,
                source=str(file_path),
                doc_type=doc_type,
                metadata={"filename": file_path.name}
            )
            
            # Store the document
            doc_id = f"{file_path.stem}_{doc_type}"
            self.documents[doc_id] = document
            
            # Save processed document
            self._save_processed_document(doc_id, document)
            
            return document
            
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {str(e)}")
            raise
            
    def _process_pdf(self, file_path: Path) -> str:
        """Process a PDF file and extract its text content."""
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
        
    def _process_spreadsheet(self, file_path: Path) -> str:
        """Process a spreadsheet file and convert it to text."""
        df = pd.read_excel(file_path) if file_path.suffix == '.xlsx' else pd.read_csv(file_path)
        return df.to_string()
        
    def _process_markdown(self, file_path: Path) -> str:
        """Process a markdown file."""
        return file_path.read_text()
        
    def _process_text(self, file_path: Path) -> str:
        """Process a plain text file."""
        return file_path.read_text()
        
    def _save_processed_document(self, doc_id: str, document: Document) -> None:
        """Save a processed document to the knowledge base."""
        processed_path = self.base_path / "processed" / f"{doc_id}.json"
        with open(processed_path, 'w') as f:
            json.dump(document.model_dump(), f, indent=2)
            
    def query_knowledge(self, query: str) -> List[Document]:
        """Query the knowledge base for relevant documents.
        
        Args:
            query: Search query string
            
        Returns:
            List of relevant Document objects
        """
        # TODO: Implement more sophisticated search
        # For now, return all documents that contain the query string
        return [
            doc for doc in self.documents.values()
            if query.lower() in doc.content.lower()
        ]
        
    def get_document(self, doc_id: str) -> Optional[Document]:
        """Retrieve a specific document by ID."""
        return self.documents.get(doc_id)
        
    def list_documents(self) -> List[str]:
        """List all document IDs in the knowledge base."""
        return list(self.documents.keys()) 