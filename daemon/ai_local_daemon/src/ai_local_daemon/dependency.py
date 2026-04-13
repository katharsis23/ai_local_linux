from fastapi import Request

from src.ai_local_daemon.wrappers.config import ConfigManager
from src.ai_local_daemon.wrappers.cache import CacheManager
from src.ai_local_daemon.config.settings import Settings

# Depends functions

def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_cache_manager(request: Request) -> CacheManager:
    return request.app.state.cache_manager


def get_config_manager(request: Request) -> ConfigManager:
    return request.app.state.config_manager