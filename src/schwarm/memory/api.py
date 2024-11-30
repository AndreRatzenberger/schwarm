"""Fluent API for memory operations."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .service import MemoryService


@dataclass
class MemorySearchQuery:
    """Query parameters for memory search."""
    query: str
    limit: Optional[int] = None
    similarity_threshold: Optional[float] = None
    metadata_filter: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Memory:
    """Represents a stored memory."""
    content: str
    metadata: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)
    similarity: Optional[float] = None


class MemoryFluentAPI:
    """Fluent interface for memory operations.
    
    Example:
        # Search memories
        memories = await agent.memory.search("Paris")
            .limit(5)
            .with_threshold(0.8)
            .execute()
            
        # Store memory
        await agent.memory.store("Important fact")
            .with_metadata({"source": "user"})
            .execute()
    """
    
    def __init__(self, service: MemoryService):
        """Initialize the memory API.
        
        Args:
            service: The underlying memory service
        """
        self._service = service
        self._reset_query()
        
    def _reset_query(self) -> None:
        """Reset the query builder state."""
        self._current_query = MemorySearchQuery(
            query="",
            limit=None,
            similarity_threshold=None,
            metadata_filter={}
        )
        self._store_content: Optional[str] = None
        self._store_metadata: Dict[str, Any] = {}
        
    def search(self, query: str) -> 'MemoryFluentAPI':
        """Start a search query.
        
        Args:
            query: The search query string
            
        Returns:
            Self for chaining
        """
        self._current_query.query = query
        return self
        
    def limit(self, count: int) -> 'MemoryFluentAPI':
        """Set the result limit.
        
        Args:
            count: Maximum number of results
            
        Returns:
            Self for chaining
        """
        self._current_query.limit = count
        return self
        
    def with_threshold(self, threshold: float) -> 'MemoryFluentAPI':
        """Set similarity threshold.
        
        Args:
            threshold: Minimum similarity score (0-1)
            
        Returns:
            Self for chaining
        """
        self._current_query.similarity_threshold = threshold
        return self
        
    def filter(self, **kwargs: Any) -> 'MemoryFluentAPI':
        """Add metadata filters.
        
        Args:
            **kwargs: Metadata key-value pairs to filter on
            
        Returns:
            Self for chaining
        """
        self._current_query.metadata_filter.update(kwargs)
        return self
        
    async def execute(self) -> List[Memory]:
        """Execute the search query.
        
        Returns:
            List of matching memories
            
        Note:
            Resets the query builder state after execution
        """
        try:
            results = await self._service.search(self._current_query)
            return results
        finally:
            self._reset_query()
            
    def store(self, content: str) -> 'MemoryFluentAPI':
        """Start a store operation.
        
        Args:
            content: The content to store
            
        Returns:
            Self for chaining
        """
        self._store_content = content
        return self
        
    def with_metadata(self, metadata: Dict[str, Any]) -> 'MemoryFluentAPI':
        """Add metadata to stored memory.
        
        Args:
            metadata: Key-value pairs of metadata
            
        Returns:
            Self for chaining
        """
        self._store_metadata.update(metadata)
        return self
        
    async def execute_store(self) -> Memory:
        """Execute the store operation.
        
        Returns:
            The stored memory
            
        Raises:
            ValueError: If no content was set
            
        Note:
            Resets the builder state after execution
        """
        if not self._store_content:
            raise ValueError("No content set for storage")
            
        try:
            memory = await self._service.store(
                content=self._store_content,
                metadata=self._store_metadata
            )
            return memory
        finally:
            self._reset_query()
            
    async def clear(
        self,
        before: Optional[datetime] = None,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> int:
        """Clear memories matching criteria.
        
        Args:
            before: Optional timestamp to clear memories before
            metadata_filter: Optional metadata criteria
            
        Returns:
            Number of memories cleared
        """
        return await self._service.clear(
            before=before,
            metadata_filter=metadata_filter
        )
        
    async def get_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics.
        
        Returns:
            Dictionary of memory statistics
        """
        return await self._service.get_stats()
