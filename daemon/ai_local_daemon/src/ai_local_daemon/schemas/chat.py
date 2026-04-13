from pydantic import BaseModel
from typing import List


class ChatMetaResponse(BaseModel):
    id: str
    title: str
    last_edited: str
    file_size: int
    message_count: int


class ChatResponse(BaseModel):
    metadata: ChatMetaResponse
    messages: List = []

class CreateChatRequest(BaseModel):
    title: str = "New Chat"