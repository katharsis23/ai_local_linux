# from tests.client import client
from src.ai_local_daemon.config.settings import Settings
from src.ai_local_daemon.wrappers.config import ConfigManager


def test_config_loads(config_manager):
    settings = config_manager.load_settings()

    assert settings.model_name == "gpt3"
    assert settings.temperature == 0.5

    assert "chats" in settings.save_chat_directory


def test_system_prompt(config_manager):
    system_prompt = config_manager.get_system_prompt()

    assert system_prompt is not None
    assert "## GENERAL BEHAVIOR" in system_prompt
    assert "## TOOL USAGE PROTOCOL" in system_prompt


def test_config_reload(config_manager):
    s1 = config_manager.load_settings()
    s2 = config_manager.reload()

    assert s1 is not s2