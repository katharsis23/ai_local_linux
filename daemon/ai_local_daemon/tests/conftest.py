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
    """Mocked config manager with temp config file"""
    config_path = temp_dir / "settings.json"

    # create minimal config file
    config_path.write_text("""{
      "model_name": "llama3",
      "temperature": 0.5,
      "save_chat_directory": "%s"
    }""" % (temp_dir / "chats"))

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