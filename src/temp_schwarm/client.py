"""Single point for Temporal connection management."""

from dataclasses import dataclass
from typing import Optional

from temporalio.client import Client


@dataclass
class TemporalConfig:
    """Configuration for Temporal connection."""

    host: str = "localhost"
    port: int = 7233
    namespace: str = "default"
    task_queue: str = "schwarm-task-queue"


class TemporalClientManager:
    """Manages Temporal client connections."""

    _instance: Optional["TemporalClientManager"] = None
    _client: Client | None = None

    def __new__(cls) -> "TemporalClientManager":
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def get_client(self, config: TemporalConfig | None = None) -> Client:
        """Get or create Temporal client."""
        if self._client is None:
            cfg = config or TemporalConfig()
            self._client = await Client.connect(f"{cfg.host}:{cfg.port}", namespace=cfg.namespace)
        return self._client
