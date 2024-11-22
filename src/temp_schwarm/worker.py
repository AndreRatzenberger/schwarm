"""Worker implementation for running workflows and activities."""

from dataclasses import dataclass
from typing import Any

from temporalio.worker import Worker

from temp_schwarm.client import TemporalClientManager, TemporalConfig


@dataclass
class WorkerConfig:
    """Configuration for worker setup."""

    task_queue: str
    workflows: list[Any]  # Type[WorkflowDefinition] not needed, Any works fine
    activities: list[Any]
    temporal_config: TemporalConfig | None = None


class SchwarmWorker:
    """Runs workflows and activities."""

    def __init__(self, config: WorkerConfig):
        """Initialize worker with configuration."""
        self.config = config
        self._worker: Worker | None = None

    async def start(self) -> None:
        """Start the worker."""
        if self._worker is None:
            # Get client from manager
            client = await TemporalClientManager().get_client(self.config.temporal_config)

            # Create worker
            self._worker = Worker(
                client,
                task_queue=self.config.task_queue,
                workflows=self.config.workflows,
                activities=self.config.activities,
            )

            # Start worker
            await self._worker.run()

    async def shutdown(self) -> None:
        """Shutdown the worker."""
        if self._worker:
            await self._worker.shutdown()
            self._worker = None
