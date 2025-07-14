from datetime import datetime
from typing import List, Optional, Dict, Any

from loguru import logger
from pydantic import BaseModel, Field

from open_notebook.domain.base import ObjectModel, RecordModel
from open_notebook.database.repository import repo_query
from open_notebook.exceptions import DatabaseOperationError


class Notebook(ObjectModel):
    name: str = Field(description="Notebook name")
    description: Optional[str] = Field(default=None, description="Notebook description")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    table_name: str = "notebook"

    def get_sources(self) -> List["Source"]:
        """Get all sources in this notebook."""
        try:
            result = repo_query(
                f"SELECT VALUE ->source FROM (SELECT * FROM notebook_source WHERE in = {self.id})"
            )
            return [Source.get(source_id) for source_id in result]
        except Exception as e:
            logger.error(f"Error fetching sources for notebook {self.id}: {str(e)}")
            raise DatabaseOperationError(e)

    def get_notes(self) -> List["Note"]:
        """Get all notes in this notebook."""
        try:
            result = repo_query(f"SELECT * FROM note WHERE notebook = {self.id}")
            return [Note(**note) for note in result]
        except Exception as e:
            logger.error(f"Error fetching notes for notebook {self.id}: {str(e)}")
            raise DatabaseOperationError(e)

    def add_source(self, source: "Source") -> None:
        """Add a source to this notebook."""
        if not source.id:
            source.save()
        self.relate("notebook_source", source.id)

    def remove_source(self, source: "Source") -> None:
        """Remove a source from this notebook."""
        try:
            repo_query(
                f"DELETE FROM notebook_source WHERE in = {self.id} AND out = {source.id}"
            )
        except Exception as e:
            logger.error(f"Error removing source from notebook: {str(e)}")
            raise DatabaseOperationError(e)


class Source(ObjectModel):
    title: str = Field(description="Source title")
    description: Optional[str] = Field(default=None, description="Source description")
    url: Optional[str] = Field(default=None, description="Source URL")
    content: Optional[str] = Field(default=None, description="Source content")
    full_text: Optional[str] = Field(default=None, description="Full extracted text")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    has_document: bool = Field(default=False, description="Whether source has an attached document")
    is_processed: bool = Field(default=False, description="Whether source has been processed")
    
    table_name: str = "source"

    def get_notes(self) -> List["Note"]:
        """Get all notes for this source."""
        try:
            result = repo_query(f"SELECT * FROM note WHERE source = {self.id}")
            return [Note(**note) for note in result]
        except Exception as e:
            logger.error(f"Error fetching notes for source {self.id}: {str(e)}")
            raise DatabaseOperationError(e)

    def get_notebooks(self) -> List[Notebook]:
        """Get all notebooks containing this source."""
        try:
            result = repo_query(
                f"SELECT VALUE <-notebook_source FROM (SELECT * FROM notebook_source WHERE out = {self.id})"
            )
            return [Notebook.get(notebook_id) for notebook_id in result]
        except Exception as e:
            logger.error(f"Error fetching notebooks for source {self.id}: {str(e)}")
            raise DatabaseOperationError(e)


class Note(ObjectModel):
    content: str = Field(description="Note content")
    notebook: str = Field(description="Notebook ID this note belongs to")
    source: Optional[str] = Field(default=None, description="Source ID this note references")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    full_text: Optional[str] = Field(default=None, description="Full text for embeddings")
    
    table_name: str = "note"

    def get_notebook(self) -> Notebook:
        """Get the notebook this note belongs to."""
        return Notebook.get(self.notebook)

    def get_source(self) -> Optional[Source]:
        """Get the source this note references."""
        if self.source:
            return Source.get(self.source)
        return None

    def _prepare_save_data(self) -> Dict[str, Any]:
        """Prepare data for saving, ensuring full_text is set."""
        data = super()._prepare_save_data()
        if not self.full_text:
            data["full_text"] = self.content
        return data


class ChatSession(ObjectModel):
    name: str = Field(description="Chat session name")
    notebook: str = Field(description="Notebook ID this chat session belongs to")
    model_name: str = Field(description="AI model used for this session")
    messages: List[Dict[str, str]] = Field(default_factory=list, description="Chat messages")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    table_name: str = "chat_session"

    def get_notebook(self) -> Notebook:
        """Get the notebook this chat session belongs to."""
        return Notebook.get(self.notebook)

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the chat session."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

    def get_context_notes(self, query: str, limit: int = 5) -> List[Note]:
        """Get relevant notes for the chat context using similarity search."""
        try:
            # This would use vector similarity search in production
            # For now, return recent notes from the same notebook
            result = repo_query(
                f"SELECT * FROM note WHERE notebook = {self.notebook} ORDER BY created DESC LIMIT {limit}"
            )
            return [Note(**note) for note in result]
        except Exception as e:
            logger.error(f"Error fetching context notes: {str(e)}")
            return []


class Settings(RecordModel):
    """Application settings stored as a singleton record."""
    gemini_api_key: Optional[str] = "AIzaSyAcw-QQX3JyXB6OAYUOnsRVUsRE-XwJUow"
    default_model: str = "gemini-1.5-pro"
    default_temperature: float = 0.7
    max_tokens: int = 4000

    surrealdb_url: str = "ws://localhost:8000"
    surrealdb_namespace: str = "opennotebook"
    surrealdb_database: str = "main"
    surrealdb_username: str = "root"
    surrealdb_password: str = "root"

    record_id: str = "settings:main"

    def get_api_key(self, provider: str) -> Optional[str]:
        if provider.lower() == "gemini":
            return self.gemini_api_key
        return None

    def has_api_key(self, provider: str) -> bool:
        return bool(self.get_api_key(provider))


# Import to resolve forward references
from open_notebook.domain.models import Source, Note  # noqa: E402
