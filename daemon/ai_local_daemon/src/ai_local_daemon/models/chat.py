import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4
from src.ai_local_daemon.models.message import Message


class ChatMetadata:
    def __init__(
        self,
        last_edited: datetime,
        file_size: int = 0,
        message_count: int = 0,
        title: str = "",
        id_: str = "",
        **kwargs: Any,
    ):
        self.last_edited = last_edited
        self.file_size = file_size
        self.message_count = message_count
        self.title = title
        self.id_ = id_

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatMetadata":
        return cls(
            last_edited=datetime.fromisoformat(data["last_edited"]),
            file_size=data.get("file_size", 0),
            message_count=data.get("message_count", 0),
            title=data.get("title", ""),
            id_=data.get("id", data.get("id_", "")),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "last_edited": self.last_edited.isoformat(),
            "file_size": self.file_size,
            "message_count": self.message_count,
            "title": self.title,
            "id": self.id_,           # Use "id" for JSON compatibility
        }


class Chat:
    def __init__(
        self,
        path: Optional[str] = None,
        title: Optional[str] = None,
    ):
        if not path:
            path = f"chat_{uuid4().hex}.json"

        self.path = path
        self._messages: Optional[List[Message]] = None

        filename = os.path.basename(self.path)
        self.id_: str = filename.removeprefix("chat_").removesuffix(".json")

        self.title = title or f"Chat {self.id_[:8]}"

        # Initialize metadata
        self.metadata = ChatMetadata(
            last_edited=datetime.now(),
            file_size=0,
            message_count=0,
            title=self.title,
            id_=self.id_,
        )

    @property
    def messages(self) -> List[Message]:
        if self._messages is None:
            self._messages = self._load()
        return self._messages

    def _load(self) -> List[Message]:
        if not os.path.exists(self.path):
            return []

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []  # handle empty file

                data = json.loads(content)
        except Exception:
            return []  # don't crash

        if "metadata" in data:
            self.metadata = ChatMetadata.from_dict(data["metadata"])
            self.title = self.metadata.title

        return [Message.from_dict(m) for m in data.get("messages", [])]

    def add(self, message: Message) -> None:
        self.messages.append(message)
        self.metadata.message_count = len(self.messages)
        self.metadata.last_edited = datetime.now()

    def save(self) -> None:
        dir_ = os.path.dirname(self.path)
        if dir_:
            os.makedirs(dir_, exist_ok=True)

        # IMPORTANT: avoid lazy load here
        messages = self._messages if self._messages is not None else []

        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "id": self.id_,
                    "title": self.title,
                    "metadata": self.metadata.to_dict(),
                    "messages": [m.to_dict() for m in messages],
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

    def trim(self, max_messages: int = 50) -> None:
        if len(self.messages) > max_messages:
            self._messages = self.messages[-max_messages:]
            self.metadata.message_count = len(self._messages)