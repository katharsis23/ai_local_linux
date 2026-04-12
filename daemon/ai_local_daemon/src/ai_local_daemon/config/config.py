import os
import json
from pydantic_settings import BaseSettings
from src.ai_local_daemon.config.settings import Settings


DEFAULT_CONFIG_CONTENT = """{
  // AI model name (ollama)
  "model_name": "llama3",

  // Sampling temperature (0.0 - deterministic, 1.0+ creative)
  "temperature": 0.7,

  // Where chat history is stored
  "save_chat_directory": "~/.local/share/ai_local_daemon/chats",

  // Default system prompt injected into every request
  "default_prompt": "You are a helpful local AI assistant.",

  // Allowed directories AI can read
  "white_list_directories": ["~/projects"],

  // Blocked directories (takes priority over whitelist)
  "black_list_directories": ["/etc", "/root"],

  // Allowed shell commands (prefix match)
  "white_list_commands": ["ls", "cat", "echo"],

  // Max file size AI can read (bytes)
  "max_file_size": 200000,

  // Max files per request
  "max_files": 20
}
"""


class Config(BaseSettings):

    # Value that only accessed by 'get_settings_path' method that normalizes
    __settings_file_path: str = "~/.config/ai_local_daemon/settings.json"

    def get_settings(self) -> Settings:
        path = os.path.expanduser(self.settings_file_path)

        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(DEFAULT_CONFIG_CONTENT)

        # remove comments before loading JSON
        with open(path, "r") as f:
            raw = f.read()

        clean = "\n".join(
            line for line in raw.splitlines()
            if not line.strip().startswith("//")
        )

        data = json.loads(clean or "{}")

        return Settings(**data)
    
    def set_settings_file_path(self, new_path: str) -> "Config":
        self.__settings_file_path = new_path
        return self
    
    @property
    def settings_file_path(self) -> str:
        return os.path.expanduser(self.__settings_file_path)


CONFIG = Config()