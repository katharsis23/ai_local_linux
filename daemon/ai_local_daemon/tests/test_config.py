from client import client
from src.ai_local_daemon.config.settings import Settings
from src.ai_local_daemon.wrappers.config import ConfigManager


def test_config_loads(config_manager):
    settings = config_manager.load_settings()

    assert settings.model_name == "llama3"
    assert settings.temperature == 0.5

    assert settings.save_chat_directory == "/tmp/chats"
    assert settings.default_prompt == "You are a helpful local AI assistant."
    assert settings.white_list_directories == []
    assert settings.black_list_directories == []
    assert settings.white_list_commands == []
    assert settings.max_file_size == 200_000
    assert settings.max_files == 20


def test_system_prompt(config_manager):
    system_prompt = config_manager.get_system_prompt()

    assert system_prompt is not None
    assert "## GENERAL BEHAVIOR" in system_prompt
    assert "## TOOL USAGE PROTOCOL" in system_prompt