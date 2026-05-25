import os
import json
import tempfile
import shutil
from typing import Any, Dict

from pydantic_settings import BaseSettings
from src.ai_local_daemon.config.settings import Settings, SYSTEM_PROMPT


DEFAULT_CONFIG: Dict[str, Any] = {
    "model_name": "llama3",
    "temperature": 0.7,
    "save_chat_directory": "~/.local/share/ai_local_daemon/chats",
    "default_prompt": SYSTEM_PROMPT,
    "white_list_directories": ["~/projects"],
    "black_list_directories": ["/etc", "/root"],
    "white_list_commands": ["ls", "cat", "echo", "cd", "pwd", "whoami"],
    "max_file_size": 200000,
    "max_files": 20,
}


class Config(BaseSettings):
    __settings_file_path: str = "~/.config/ai_local_daemon/settings.json"

    # =========================
    # Core Load
    # =========================

    def get_settings(self) -> Settings:
        data = self._ensure_and_load()
        return Settings(**data)

    def _ensure_and_load(self) -> Dict[str, Any]:
        path = self.settings_file_path

        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            self._atomic_write(DEFAULT_CONFIG)

        return self._read_json()

    def _read_json(self) -> Dict[str, Any]:
        path = self.settings_file_path

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()

                if not content:
                    return {}

                return json.loads(content)

        except json.JSONDecodeError:
            # fallback: reset config
            self._atomic_write(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()

    # =========================
    # Safe Write
    # =========================

    def _atomic_write(self, data: Dict[str, Any]) -> None:
        path = self.settings_file_path
        dir_ = os.path.dirname(path)

        os.makedirs(dir_, exist_ok=True)

        with tempfile.NamedTemporaryFile(
            "w", delete=False, dir=dir_, encoding="utf-8"
        ) as tmp:
            json.dump(data, tmp, indent=2, ensure_ascii=False)
            tmp_path = tmp.name

        shutil.move(tmp_path, path)

    def _update(self, updater) -> None:
        data = self._ensure_and_load()

        updater(data)  # mutate dict safely

        self._atomic_write(data)

    # =========================
    # Public Mutations
    # =========================

    def add_white_list_dir(self, directory: str) -> None:
        directory = os.path.expanduser(directory)

        def updater(data):
            dirs = data.setdefault("white_list_directories", [])
            if directory not in dirs:
                dirs.append(directory)

        self._update(updater)

    def remove_white_list_dir(self, directory: str) -> None:
        directory = os.path.expanduser(directory)

        def updater(data):
            dirs = data.get("white_list_directories", [])
            if directory in dirs:
                dirs.remove(directory)

        self._update(updater)

    def add_white_list_command(self, command: str) -> None:
        def updater(data):
            cmds = data.setdefault("white_list_commands", [])
            if command not in cmds:
                cmds.append(command)

        self._update(updater)

    def remove_white_list_command(self, command: str) -> None:
        def updater(data):
            cmds = data.get("white_list_commands", [])
            if command in cmds:
                cmds.remove(command)

        self._update(updater)

    def set_value(self, key: str, value: Any) -> None:
        def updater(data):
            data[key] = value

        self._update(updater)

    # =========================
    # Path Management
    # =========================

    def set_settings_file_path(self, new_path: str) -> "Config":
        self.__settings_file_path = new_path
        return self

    @property
    def settings_file_path(self) -> str:
        return os.path.expanduser(self.__settings_file_path)


CONFIG = Config()