from fastapi import Request

from src.ai_local_daemon.wrappers.config import ConfigManager
from src.ai_local_daemon.wrappers.cache import CacheManager
from src.ai_local_daemon.config.settings import Settings
from src.ai_local_daemon.internal.approval import ApprovalManager
from src.ai_local_daemon.internal.tool_calling import (
    DirectoryManager, FileManager
)

# Depends functions

def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_cache_manager(request: Request) -> CacheManager:
    return request.app.state.cache_manager


def get_config_manager(request: Request) -> ConfigManager:
    return request.app.state.config_manager


def get_approval_manager(request: Request) -> ApprovalManager:
    return request.app.state.approval_manager


def get_file_manager(request: Request) -> FileManager:
    return request.app.state.file_manager


def get_directory_manager(request: Request) -> DirectoryManager:
    return request.app.state.directory_manager