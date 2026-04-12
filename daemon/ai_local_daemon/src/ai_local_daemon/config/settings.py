import os
from pydantic import BaseModel, field_validator
from typing import List, Optional
import src.ai_local_daemon.helper as helper





class Settings(BaseModel):
    model_name: str = "llama3"
    temperature: float = 0.7

    save_chat_directory: Optional[str] = "~/.local/share/ai_local_daemon/chats"
    default_prompt: str = "You are a helpful assistant."

    white_list_directories: List[str] = []
    black_list_directories: List[str] = []
    white_list_commands: List[str] = []

    max_file_size: int = 200_000
    max_files: int = 20

    @field_validator(
        "white_list_directories",
        "black_list_directories",
        mode="before"
    )
    @classmethod
    def normalize_dirs(cls, value):
        if isinstance(value, str):
            value = value.split(",")

        return [helper.normalize_path(v) for v in value]

    @field_validator("save_chat_directory", mode="before")
    @classmethod
    def normalize_chat_dir(cls, value):
        if value:
            return helper.normalize_path(value)
        return value