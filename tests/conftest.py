
import os
import pytest
from schwarm.models.message import Message

from unittest.mock import  Mock

from schwarm.provider.base.base_llm_provider import BaseLLMProvider

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

@pytest.fixture
def mock_llm_provider():
    provider = Mock(spec=BaseLLMProvider)
    def mock_complete(*args, **kwargs) -> Message: # type: ignore
        return Message(role="assistant", content="Test response")
    
    provider.complete = Mock(side_effect=mock_complete)
    return provider