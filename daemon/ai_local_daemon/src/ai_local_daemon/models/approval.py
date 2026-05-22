from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional, Final
from uuid import uuid4, UUID
from datetime import datetime
import os
import asyncio


class ApprovalRequest(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    type_: Literal["file", "directory", "command"]
    user: Optional[str] = Field(default=None)
    path: Optional[str] = Field(default=None)
    command: Optional[str] = Field(default=None)
    created_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    approved: Optional[bool] = None

    @field_validator('path')
    def is_exist(cls, path: str):
        if path is None:
            return path
        if os.path.exists(path):
            return path
        else:
            raise FileNotFoundError("Path does not exist")


class ApprovalState:
    def __init__(self, request: ApprovalRequest):
        self.request = request
        self.event = asyncio.Event()
