"""WebAgent class definition."""

from typing import Literal

from pydantic import Field

from schwarm.models.types import Agent, Result


class WebAgent(Agent):
    """Agent that can surf the web."""

    query: str = Field(default="", title="Queries to search for")
    mode: Literal["search", "scrape"] = Field(default="search", title="Mode of operation")
    transfer_to: Agent | None = Field(..., title="Agent to transfer the result to")

    def search(self, query: str) -> Result:
        """Search the web for a query."""
        return Result()

    def scrape_url(self, url: str) -> Result:
        """Scrape the content of a URL."""
        return Result()

    def _instructions(self) -> str:
        if self.mode == "search":
            return f"Search for {self.query}."
        else:
            return f"Scrape {self.query}."

    def __init__(
        self, name: str, query: str = "", mode: Literal["search", "scrape"] = "search", transfer_to: Agent | None = None
    ):
        """Initialize the WebAgent."""
        super().__init__(name=name)
        self.query = query
        self.mode = mode
        self.transfer_to = transfer_to
