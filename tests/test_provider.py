

import os
import pytest

from schwarm.models.message import Message
from schwarm.provider.litellm_provider import ConfigurationError, LiteLLMConfig, LiteLLMProvider

from tests.conftest import OPENAI_API_KEY

@pytest.mark.asyncio
async def test_provider_without_config_and_no_envvars():
    try:
        old_environ = os.environ
        os.environ = {} # clear the environment variable

        LiteLLMProvider("gpt-4o-mini")
        
        assert False
    except Exception as e:
        assert isinstance(e, ConfigurationError)
    finally:
        os.environ = old_environ # type: ignore


@pytest.mark.asyncio
async def test_provider_without_config_and_envvars():
    try:
        old_environ = os.environ
        os.environ = {'OPENAI_API_KEY': 'api-key'}

        LiteLLMProvider("gpt-4o-mini")
        
        assert True
    except Exception:
        assert False
    finally:
        os.environ = old_environ # type: ignore

@pytest.mark.asyncio
async def test_provider_without_config_and_wrong_envvars():
    try:
        old_environ = os.environ
        os.environ = {'ANTHROPIC_API_KEY': 'api-key'}

        LiteLLMProvider("gpt-4o-mini")
        
        assert False
    except Exception:
        assert True
    finally:
        os.environ = old_environ # type: ignore



@pytest.mark.asyncio
async def test_provider_test_connection_without_config_and_envvars():
    try:
        old_environ = os.environ
        os.environ = {'OPENAI_API_KEY': 'api-key'}

        provider = LiteLLMProvider("gpt-4o-mini")
        
        result = provider.test_connection()
        assert result == False
    except Exception:
        assert False
    finally:
        os.environ = old_environ # type: ignore

@pytest.mark.asyncio
async def test_provider_test_connection_without_config_and_good_key():
    try:
        old_environ = os.environ
        os.environ = {'OPENAI_API_KEY': OPENAI_API_KEY}

        provider = LiteLLMProvider("gpt-4o-mini")
        
        result = provider.test_connection()
        assert result == True
    except Exception:
        assert False
    finally:
        os.environ = old_environ # type: ignore

@pytest.mark.asyncio
async def test_provider_completion_without_config_and_good_key():
    try:
        old_environ = os.environ
        os.environ = {'OPENAI_API_KEY': OPENAI_API_KEY}

        provider = LiteLLMProvider("gpt-4o-mini")

        msg = Message(role="user", content="Hallo!")
        result = provider.complete([msg])
 
        assert result.name == "gpt-4o-mini"
    except Exception:
        assert False
    finally:
        os.environ = old_environ # type: ignore

@pytest.mark.asyncio
async def test_provider_completion_without_config_and_good_key_with_cache():
    try:
        old_environ = os.environ
        os.environ = {'OPENAI_API_KEY': OPENAI_API_KEY}

        provider = LiteLLMProvider("gpt-4o-mini", LiteLLMConfig(enable_cache=True))

        msg_text = "Hallo! I just wanted to test the cache of my application"
        msg = Message(role="user", content=msg_text)

        result = provider.complete([msg])
 
        assert result.name == "gpt-4o-mini"

        result = provider.complete([msg])
 
        assert result.name == "gpt-4o-mini"
    except Exception:
        assert False
    finally:
        os.environ = old_environ # type: ignore


@pytest.mark.asyncio
async def test_provider_with_bad_config():
    try:
        old_environ = os.environ
        os.environ = {'': ''}

        provider = LiteLLMProvider("gpt-4o-mini", LiteLLMConfig(api_key="blubb",enable_cache=True))
        assert False
        msg_text = "Hallo! I just wanted to test the cache of my application"
        msg = Message(role="user", content=msg_text)
        
        result = await provider.complete([msg])
 
        assert result.name == "gpt-4o-mini"
    except Exception:
        assert True
    finally:
        os.environ = old_environ # type: ignore

@pytest.mark.asyncio
async def test_provider_with_bad_config_with_fallback_to_env():
    try:
        old_environ = os.environ
        os.environ = {'OPENAI_API_KEY': OPENAI_API_KEY}

        provider = LiteLLMProvider("gpt-4o-mini", LiteLLMConfig(api_key="blubb",enable_cache=True))
 
        msg_text = "Hallo! I just wanted to test the cache of my application"
        msg = Message(role="user", content=msg_text)
        
        result = provider.complete([msg])
 
        assert result.name == "gpt-4o-mini"
    except Exception:
        assert False
    finally:
        os.environ = old_environ # type: ignore


@pytest.mark.asyncio
async def test_provider_with_good_config():
    try:
        old_environ = os.environ
        os.environ = {'': ''}

        provider = LiteLLMProvider("gpt-4o-mini", LiteLLMConfig(api_key=OPENAI_API_KEY,enable_cache=True))
 
        msg_text = "Hallo! I just wanted to test the cache of my application"
        msg = Message(role="user", content=msg_text)
        
        result = provider.complete([msg])
 
        assert result.name == "gpt-4o-mini"
    except Exception:
        assert False
    finally:
        os.environ = old_environ # type: ignore

    
