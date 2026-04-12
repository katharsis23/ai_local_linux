from src.ai_local_daemon.config.config import Config
from src.ai_local_daemon.config.settings import Settings


class ConfigManager:
    def __init__(self, config: Config):
        self.config = config
        self._settings: Settings | None = None

    # rarely needed, but keeps abstraction clean
    def load_config(self) -> Config:
        return self.config

    def load_settings(self) -> Settings:
        if self._settings is None:
            self._settings = self.config.get_settings()
        return self._settings

    def reload(self) -> Settings:
        self._settings = None
        return self.load_settings()

    # convenience accessors
    @property
    def settings(self) -> Settings:
        return self.load_settings()