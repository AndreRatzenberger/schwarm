"""Base telemetry exporter interface."""

from abc import ABC, abstractmethod
from typing import Any

from schwarma_core.events import Event


class TelemetryExporter(ABC):
    """Abstract base class for telemetry exporters.

    Telemetry exporters handle the recording and exporting of telemetry data
    from various system events. Each exporter implements a specific storage
    or transmission mechanism.

    Example:
        class FileExporter(TelemetryExporter):
            async def initialize(self):
                self._file = open("telemetry.log", "a")

            async def export_event(self, event):
                self._file.write(f"{event.type}: {event.data}\n")

            async def shutdown(self):
                self._file.close()
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the exporter.

        This method should handle any setup required for the exporter,
        such as establishing connections or creating files.

        Returns:
            None
        """
        pass

    @abstractmethod
    async def export_event(self, event: Event) -> None:
        """Export a telemetry event.

        Args:
            event: The event to export

        Returns:
            None
        """
        pass

    @abstractmethod
    async def export_span(
        self,
        name: str,
        start_time: float,
        end_time: float,
        attributes: dict[str, Any],
        parent_id: str | None = None,
    ) -> None:
        """Export a telemetry span.

        Args:
            name: Name of the span
            start_time: Start time in seconds
            end_time: End time in seconds
            attributes: Span attributes
            parent_id: Optional ID of parent span

        Returns:
            None
        """
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the exporter.

        This method should handle any cleanup required,
        such as closing connections or files.

        Returns:
            None
        """
        pass

    async def __aenter__(self) -> "TelemetryExporter":
        """Initialize the exporter when used as a context manager.

        Returns:
            Self for use in context manager
        """
        await self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Shutdown the exporter when exiting context manager.

        Args:
            exc_type: Exception type if an error occurred
            exc_val: Exception value if an error occurred
            exc_tb: Exception traceback if an error occurred

        Returns:
            None
        """
        await self.shutdown()
