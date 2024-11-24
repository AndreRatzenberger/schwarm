"""MongoDB provider for storing system events in a MongoDB database."""

from datetime import datetime
from typing import Any

from loguru import logger
from pydantic import Field
from pymongo import MongoClient

from schwarm.events.event import Event
from schwarm.provider.base.base_event_handle_provider import BaseEventHandleProvider, BaseEventHandleProviderConfig
from schwarm.provider.provider_context import ProviderContext


class MongoDBConfig(BaseEventHandleProviderConfig):
    """Configuration for the MongoDB provider."""

    mongo_uri: str = Field(default="mongodb://ara:ara@127.0.0.1:27017/", description="MongoDB connection URI")
    database_name: str = Field(default="schwarm_events", description="MongoDB database name")
    collection_name: str = Field(default="events", description="MongoDB collection name")
    provider_id: str = Field(default="mongodb", description="Provider ID")


class MongoDBProvider(BaseEventHandleProvider):
    """MongoDB provider that stores system events in a MongoDB database."""

    config: MongoDBConfig

    def __init__(self, config: MongoDBConfig, **data: Any):
        super().__init__(config, **data)
        self._mongo_client = MongoClient(self.config.mongo_uri)
        self._db = self._mongo_client[self.config.database_name]
        self._collection = self._db[self.config.collection_name]
        logger.info(f"Successfully connected to MongoDB at {self.config.mongo_uri}")

    def handle_event(self, event: Event) -> ProviderContext | None:
        """Handle events by storing them in MongoDB.

        Args:
            event: The event to handle and store

        Returns:
            The provider context if the event payload is a ProviderContext, None otherwise
        """
        # Always log the event

        # Early return if MongoDB isn't initialized
        if self._collection is None:
            logger.error("MongoDB collection not initialized")
            return self._get_provider_context(event)

        try:
            # Convert event to dictionary and add timestamp
            event_dict = {
                "timestamp": datetime.utcnow(),
                "event_type": str(event.type),  # Convert EventType to string for MongoDB storage
                "payload": self._serialize_payload(event.payload),
            }

            # Store in MongoDB
            self._collection.insert_one(event_dict)
            logger.debug(f"Stored event {event.type} in MongoDB")
        except Exception as e:
            logger.error(f"Failed to store event in MongoDB: {e!s}")

        return self._get_provider_context(event)

    def _serialize_payload(self, payload: Any) -> Any:
        """Serialize payload for MongoDB storage."""
        if hasattr(payload, "model_dump"):
            return payload.model_dump()
        return str(payload)

    def _get_provider_context(self, event: Event) -> ProviderContext | None:
        """Extract ProviderContext from event if available."""
        if isinstance(event.payload, ProviderContext):
            return event.payload
        return None
