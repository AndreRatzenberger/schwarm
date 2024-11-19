
from pydantic import ValidationError
import pytest

from schwarm.provider.models import BaseLLMProviderConfig



@pytest.mark.asyncio
async def test_provider_config_wrong_api_base():
    try:
        BaseLLMProviderConfig(api_key="api-key",api_base="nouri")
        
        assert False
    except Exception as e:
        assert isinstance(e, ValidationError)

@pytest.mark.asyncio
async def test_provider_config_goog_api_base():
    try:
        BaseLLMProviderConfig(api_key="api-key",api_base="https://pytest.com")
        
        assert True
    except Exception:
        assert False