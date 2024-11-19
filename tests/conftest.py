
import pytest
from schwarm.models.message import Message
from schwarm.provider.provider_base import LLMProvider
from unittest.mock import AsyncMock, Mock

OPENAI_API_KEY = ""

@pytest.fixture
def mock_llm_provider():
    provider = Mock(spec=LLMProvider)
    async def mock_complete(*args, **kwargs) -> Message: # type: ignore
        return Message(role="assistant", content="Test response")
    
    # {
    #         "role": "assistant",
    #         "content": "Test response",
    #         "tool_calls": []
    #     }
    provider.complete = AsyncMock(side_effect=mock_complete)
    return provider