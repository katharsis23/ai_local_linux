from src.ai_local_daemon.config.config import Config
from src.ai_local_daemon.config.settings import Settings, SYSTEM_PROMPT


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
    
    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT.format(
            model=self.settings.model_name
        )
    
    def build_prompt(self) -> str:
        # Combines the user prompt and system prompt
        return f"""
            {self.get_system_prompt()}

            {self.settings.default_prompt}

            User preferences:
            {self.settings.default_prompt}
            """
