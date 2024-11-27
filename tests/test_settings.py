import os
import pytest
from unittest.mock import mock_open, patch


from schwarm.utils.settings import Settings, get_config, APP_SETTINGS

local_scope_settings = Settings(env_path=".env_test")

@pytest.fixture
def clean_env():
    """Fixture to provide clean environment variables."""
    global local_scope_settings
    local_scope_settings = Settings(env_path=".env_test")
    old_environ = dict(os.environ)
    os.environ.clear()
    yield
    os.environ.clear()
    os.environ.update(old_environ)
    os.remove(".env_test")

@pytest.mark.asyncio
def test_get_config_with_default(clean_env): # type: ignore
    """Test get_config returns default when key not found."""
    assert local_scope_settings.SYSTEM_ROLE == "system"
    assert get_config("NON_EXISTENT_KEY", default="default_value") == "default_value"


def test_get_config_with_env_value(clean_env): # type: ignore
    """Test get_config returns environment value when set."""
    with patch.dict(os.environ, {"TEST_KEY": "test_value"}):
        assert get_config("TEST_KEY", default="default") == "test_value"


def test_settings_init_creates_env_file(clean_env): # type: ignore
    """Test Settings initialization creates .env file with defaults."""
    mock_env_content = ""
    with patch("builtins.open", mock_open(read_data=mock_env_content)) as mock_file:
        settings = Settings()
        
        # Verify .env file was opened for reading and writing
        mock_file.assert_any_call(".env")
        mock_file.assert_any_call(".env", "a")
        
        # Verify all defaults were written
        handle = mock_file()
        written_content = "".join(call.args[0] for call in handle.write.call_args_list)
        for key, value in settings._defaults.items(): # type: ignore
            assert f"{key}={value}" in written_content


def test_settings_init_preserves_existing_values(clean_env): # type: ignore
    """Test Settings initialization preserves existing values in .env."""
    existing_content = "DATA_FOLDER=/custom/path/\n"
    with patch("builtins.open", mock_open(read_data=existing_content)) as mock_file:
        Settings()
        
        # Verify existing value wasn't overwritten
        handle = mock_file()
        written_content = "".join(call.args[0] for call in handle.write.call_args_list)
        assert "DATA_FOLDER=/custom/path/" not in written_content


def test_settings_getattr_default_value(clean_env): # type: ignore
    """Test getting attribute returns default value when not in env."""
    with patch("builtins.open", mock_open(read_data="")):
        settings = Settings()
        assert settings.DATA_FOLDER == ".data/"


def test_settings_getattr_env_value(clean_env): # type: ignore
    """Test getting attribute returns environment value when set."""
    with patch.dict(os.environ, {"DATA_FOLDER": "/custom/path/"}):
        with patch("builtins.open", mock_open(read_data="")):
            #settings = Settings()
            assert APP_SETTINGS.DATA_FOLDER == "/custom/path/"


def test_settings_setattr_without_writeback(clean_env): # type: ignore
    """Test setting attribute without write_back enabled."""
    with patch("builtins.open", mock_open(read_data="")) as mock_file:
        settings = Settings()
        settings.DATA_FOLDER = "/new/path/"
        
        # Verify value is set in environment
        assert os.environ["DATA_FOLDER"] == "/new/path/"
        
        # Verify no write to .env file
        handle = mock_file()
        assert not any("DATA_FOLDER=/new/path/" in str(call) 
                      for call in handle.write.call_args_list)




def test_settings_writeback_control(clean_env): # type: ignore
    """Test write_back property control."""
    with patch("builtins.open", mock_open(read_data="")):
        #settings = Settings()
        
        # Test default value
        assert APP_SETTINGS.WRITE_BACK == "false"
        
        # Test setting to true
        APP_SETTINGS.WRITE_BACK = "true"
        assert APP_SETTINGS.WRITE_BACK == "true"
        
        # Test setting to false
        APP_SETTINGS.WRITE_BACK = "false"
        assert APP_SETTINGS.WRITE_BACK == "false"



