
import os
import pytest
from schwarm.models.message import Message

from unittest.mock import AsyncMock, Mock

from schwarm.provider.base.base_llm_provider import BaseLLMProvider

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

@pytest.fixture
def mock_llm_provider():
    provider = Mock(spec=BaseLLMProvider)
    async def mock_complete(*args, **kwargs) -> Message: # type: ignore
        return Message(role="assistant", content="Test response")
    
    # {
    #         "role": "assistant",
    #         "content": "Test response",
    #         "tool_calls": []
    #     }
    provider.complete = AsyncMock(side_effect=mock_complete)
    return provider