from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Literal
from datetime import datetime


@dataclass
class Chat:
    def __init__(
            self,
            last_edited: datetime,
            file_size: int = 0,
            message_count: int = 0,
            title: str = "",
            id_: str = "",
            messages: List = [],
            **kwargs: Any,
    ):
        self.last_edited = last_edited
        self.file_size = file_size
        self.message_count = message_count
        self.title = title
        self.id_ = id_
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.messages = messages

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.to_dict()})"

    @classmethod
    def from_dict(data: Dict[str, Any]):
        for key, value in data.items():
            setattr(Chat, key, value)


@dataclass
class Messages:
    def __init__(
            self,
            message: str,
            role: Literal["user", "assistant", "system"],
            chat_id: str = "",
    ):
        self.message = message
        self.role = role
        self.chat_id = chat_id

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(data: Dict[str, Any]):
        for key, value in data.items():
            setattr(Messages, key, value)
