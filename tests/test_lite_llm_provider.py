"""Tests for the LiteLLM provider."""

import os
import pytest

from schwarm.models.message import Message
from schwarm.provider.litellm_provider import ConfigurationError, LiteLLMConfig, LiteLLMProvider
from schwarm.provider.models.lite_llm_config import FeatureFlags, EnvironmentConfig

from tests.conftest import OPENAI_API_KEY


def create_config(model_id: str = "gpt-4o-mini", enable_cache: bool = False) -> LiteLLMConfig:
    """Create a LiteLLMConfig with the given parameters."""
    return LiteLLMConfig(
        model_id=model_id,
        features=FeatureFlags(
            cache=enable_cache,
            debug=False,
            mocking=False
        ),
        environment=EnvironmentConfig(
            override=False,
            variables={}
        )
    )


@pytest.mark.asyncio
async def test_provider_without_config_and_no_envvars():
    """Test provider initialization without config and no environment variables."""
    try:
        old_environ = os.environ
        os.environ = {}  # clear the environment variable

        provider = LiteLLMProvider(create_config())
        await provider.initialize()
        assert False
    except Exception as e:
        assert isinstance(e, ConfigurationError)
    finally:
        os.environ = old_environ  # type: ignore


@pytest.mark.asyncio
async def test_provider_without_config_and_envvars():
    """Test provider initialization with environment variables but no config."""
    try:
        old_environ = os.environ
        os.environ = {'OPENAI_API_KEY': 'api-key'}

        provider = LiteLLMProvider(create_config())
        await provider.initialize()
        assert True
    except Exception:
        assert False
    finally:
        os.environ = old_environ  # type: ignore


@pytest.mark.asyncio
async def test_provider_without_config_and_wrong_envvars():
    """Test provider initialization with wrong environment variables."""
    try:
        old_environ = os.environ
        os.environ = {'ANTHROPIC_API_KEY': 'api-key'}

        provider = LiteLLMProvider(create_config())
        await provider.initialize()
        assert False
    except Exception:
        assert True
    finally:
        os.environ = old_environ  # type: ignore


@pytest.mark.asyncio
async def test_provider_test_connection_without_config_and_envvars():
    """Test connection with environment variables but no config."""
    try:
        old_environ = os.environ
        os.environ = {'OPENAI_API_KEY': 'api-key'}

        provider = LiteLLMProvider(create_config())
        await provider.initialize()
        
        result = provider.test_connection()
        assert result == False
    except Exception:
        assert False
    finally:
        os.environ = old_environ  # type: ignore


@pytest.mark.asyncio
async def test_provider_test_connection_without_config_and_good_key():
    """Test connection with valid API key in environment."""
    try:
        old_environ = os.environ
        os.environ = {'OPENAI_API_KEY': OPENAI_API_KEY}

        provider = LiteLLMProvider(create_config())
        await provider.initialize()
        
        result = provider.test_connection()
        assert result == True
    except Exception:
        assert False
    finally:
        os.environ = old_environ  # type: ignore


@pytest.mark.asyncio
async def test_provider_completion_without_config_and_good_key():
    """Test completion with valid API key in environment."""
    try:
        old_environ = os.environ
        os.environ = {'OPENAI_API_KEY': OPENAI_API_KEY}

        provider = LiteLLMProvider(create_config())
        await provider.initialize()

        msg = Message(role="user", content="Hallo!")
        result = provider.complete([msg])
 
        assert result.name == "gpt-4o-mini"
    except Exception:
        assert False
    finally:
        os.environ = old_environ  # type: ignore


@pytest.mark.asyncio
async def test_provider_completion_without_config_and_good_key_with_cache():
    """Test completion with caching enabled."""
    try:
        old_environ = os.environ
        os.environ = {'OPENAI_API_KEY': OPENAI_API_KEY}

        provider = LiteLLMProvider(create_config(enable_cache=True))
        await provider.initialize()

        msg_text = "Hallo! I just wanted to test the cache of my application"
        msg = Message(role="user", content=msg_text)

        result = provider.complete([msg])
        assert result.name == "gpt-4o-mini"

        result = provider.complete([msg])
        assert result.name == "gpt-4o-mini"
    except Exception:
        assert False
    finally:
        os.environ = old_environ  # type: ignore


@pytest.mark.asyncio
async def test_provider_with_bad_config():
    """Test provider with invalid configuration."""
    try:
        old_environ = os.environ
        os.environ = {'': ''}

        config = create_config()
        config.environment.override = True
        config.environment.variables = {"OPENAI_API_KEY": "invalid-key"}

        provider = LiteLLMProvider(config)
        await provider.initialize()
        assert False

        msg = Message(role="user", content="Test message")
        result = provider.complete([msg])
        assert result.name == "gpt-4o-mini"
    except Exception:
        assert True
    finally:
        os.environ = old_environ  # type: ignore


@pytest.mark.asyncio
async def test_provider_with_bad_config_with_fallback_to_env():
    """Test provider fallback to environment variables with invalid config."""
    try:
        old_environ = os.environ
        os.environ = {'OPENAI_API_KEY': OPENAI_API_KEY}

        config = create_config(enable_cache=True)
        config.environment.override = True
        config.environment.variables = {"OPENAI_API_KEY": "invalid-key"}

        provider = LiteLLMProvider(config)
        await provider.initialize()

        msg = Message(role="user", content="Test message")
        result = provider.complete([msg])
        assert result.name == "gpt-4o-mini"
    except Exception:
        assert False
    finally:
        os.environ = old_environ  # type: ignore


@pytest.mark.asyncio
async def test_provider_with_good_config():
    """Test provider with valid configuration."""
    try:
        old_environ = os.environ
        os.environ = {'': ''}

        config = create_config(enable_cache=True)
        config.environment.override = True
        config.environment.variables = {"OPENAI_API_KEY": str(OPENAI_API_KEY)}

        provider = LiteLLMProvider(config)
        await provider.initialize()

        msg = Message(role="user", content="Test message")
        result = provider.complete([msg])
        assert result.name == "gpt-4o-mini"
    except Exception:
        assert False
    finally:
        os.environ = old_environ  # type: ignore
