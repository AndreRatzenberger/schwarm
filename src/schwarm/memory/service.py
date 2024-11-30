"""Memory service implementation with vector storage."""

from dataclasses import dataclass
from datetime import datetime
import json
from typing import Any, Dict, List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from .api import Memory, MemorySearchQuery


@dataclass
class VectorEntry:
    """Entry in the vector store."""
    content: str
    embedding: np.ndarray
    metadata: Dict[str, Any]
    created_at: datetime


class MemoryService:
    """Service for managing agent memories using vector storage.
    
    This service handles the storage and retrieval of memories using
    semantic vector search for better recall of relevant information.
    """
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        similarity_threshold: float = 0.7,
        max_memories: int = 1000
    ):
        """Initialize the memory service.
        
        Args:
            model_name: Name of the sentence transformer model
            similarity_threshold: Default similarity threshold
            max_memories: Maximum number of memories to store
        """
        self._model = SentenceTransformer(model_name)
        self._default_threshold = similarity_threshold
        self._max_memories = max_memories
        self._memories: List[VectorEntry] = []
        
    async def store(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Memory:
        """Store a new memory.
        
        Args:
            content: The text content to store
            metadata: Optional metadata to associate
            
        Returns:
            The stored memory
            
        Note:
            If max_memories is reached, oldest memories are removed
        """
        # Generate embedding
        embedding = self._model.encode(content)
        
        # Create entry
        entry = VectorEntry(
            content=content,
            embedding=embedding,
            metadata=metadata or {},
            created_at=datetime.utcnow()
        )
        
        # Add to storage
        self._memories.append(entry)
        
        # Prune if needed
        if len(self._memories) > self._max_memories:
            self._memories.sort(key=lambda x: x.created_at)
            self._memories = self._memories[-self._max_memories:]
            
        return Memory(
            content=content,
            metadata=entry.metadata,
            created_at=entry.created_at
        )
        
    async def search(
        self,
        query: MemorySearchQuery
    ) -> List[Memory]:
        """Search for relevant memories.
        
        Args:
            query: Search parameters
            
        Returns:
            List of matching memories sorted by relevance
        """
        # Generate query embedding
        query_embedding = self._model.encode(query.query)
        
        # Calculate similarities
        similarities = []
        for entry in self._memories:
            # Check metadata filter
            if query.metadata_filter:
                if not all(
                    entry.metadata.get(k) == v
                    for k, v in query.metadata_filter.items()
                ):
                    continue
                    
            # Calculate similarity
            similarity = np.dot(
                query_embedding,
                entry.embedding
            ) / (
                np.linalg.norm(query_embedding) *
                np.linalg.norm(entry.embedding)
            )
            
            # Check threshold
            threshold = query.similarity_threshold or self._default_threshold
            if similarity >= threshold:
                similarities.append((similarity, entry))
                
        # Sort by similarity
        similarities.sort(key=lambda x: x[0], reverse=True)
        
        # Apply limit
        if query.limit:
            similarities = similarities[:query.limit]
            
        # Convert to memories
        return [
            Memory(
                content=entry.content,
                metadata=entry.metadata,
                created_at=entry.created_at,
                similarity=similarity
            )
            for similarity, entry in similarities
        ]
        
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
        original_count = len(self._memories)
        
        if before or metadata_filter:
            self._memories = [
                entry for entry in self._memories
                if (not before or entry.created_at >= before) and
                (not metadata_filter or not all(
                    entry.metadata.get(k) == v
                    for k, v in metadata_filter.items()
                ))
            ]
        else:
            self._memories.clear()
            
        return original_count - len(self._memories)
        
    async def get_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics.
        
        Returns:
            Dictionary of memory statistics
        """
        return {
            "total_memories": len(self._memories),
            "max_memories": self._max_memories,
            "oldest_memory": min(
                (m.created_at for m in self._memories),
                default=None
            ),
            "newest_memory": max(
                (m.created_at for m in self._memories),
                default=None
            ),
            "total_size_bytes": sum(
                len(json.dumps(m.content)) +
                len(json.dumps(m.metadata)) +
                m.embedding.nbytes
                for m in self._memories
            )
        }
