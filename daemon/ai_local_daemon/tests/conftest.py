# conftest.py
import pytest
from pathlib import Path

from src.ai_local_daemon.config.config import Config
from src.ai_local_daemon.wrappers.config import ConfigManager
from src.ai_local_daemon.wrappers.cache import CacheManager


@pytest.fixture
def temp_dir(tmp_path: Path):
    """Temporary root directory for tests"""
    base = tmp_path / "ai_local_daemon"
    base.mkdir()
    return base


@pytest.fixture
def config_manager(temp_dir):
    config_path = temp_dir / "settings.json"

    data = {
        "model_name": "gpt3",
        "temperature": 0.5,
        "save_chat_directory": str(temp_dir / "chats"),
        "default_prompt": "You are a helpful local AI assistant.",
        "white_list_directories": ["~/projects"],
        "black_list_directories": ["/etc", "/root"],
        "white_list_commands": ["ls", "cat", "echo", "cd", "pwd", "whoami"],
        "max_file_size": 200000,
        "max_files": 20,
    }

    import json
    with open(config_path, "w") as f:
        json.dump(data, f)

    config = Config()
    config.set_settings_file_path(str(config_path))

    return ConfigManager(config)


@pytest.fixture
def cache_manager(temp_dir):
    """Mocked cache manager"""
    chat_dir = temp_dir / "chats"
    chat_dir.mkdir(exist_ok=True)

    cm = CacheManager(str(chat_dir))
    cm.setup()
    return cm