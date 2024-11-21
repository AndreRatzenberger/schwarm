"""Tests for model classes."""
from pydantic import ValidationError
import pytest

from schwarm.provider.base.base_provider import BaseProviderConfig


class TestProviderConfig(BaseProviderConfig):
    """Test provider configuration."""
    api_key: str
    api_base: str

    def __init__(self, **data):
        """Initialize with defaults."""
        data.update({
            "provider_name": "test_provider",
            "provider_type": "test",
            "provider_class": "tests.test_models.TestProviderConfig"
        })
        super().__init__(**data)


@pytest.mark.asyncio
async def test_provider_config_wrong_api_base():
    """Test validation of incorrect API base URL."""
    with pytest.raises(ValidationError):
        TestProviderConfig(
            api_key="api-key",
            api_base="nouri"  # Invalid URL
        )


@pytest.mark.asyncio
async def test_provider_config_good_api_base():
    """Test validation of correct API base URL."""
    config = TestProviderConfig(
        api_key="api-key",
        api_base="https://pytest.com"  # Valid URL
    )
    assert config.api_base == "https://pytest.com"
    assert config.api_key == "api-key"
