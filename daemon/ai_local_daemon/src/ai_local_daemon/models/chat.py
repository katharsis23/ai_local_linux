import json
import os
import time
from typing import List, Optional
from .message import Message
from uuid import uuid4
from typing_extensions import Final


class Chat:
    def __init__(
        self,
        path: Optional[str] = None,
        title: Optional[str] = None,
        metadata: Optional[dict] = None
    ):
        if not path:
            path = f"chat_{uuid4()}.json"

        self.path = path
        self._messages: Optional[List[Message]] = None

        filename = os.path.basename(self.path)
        self.id_: Final[str] = filename.removeprefix("chat_").removesuffix(".json")

        self.title = title or self.id_

        self.metadata = metadata or {
            "created_at": time.time(),
            "updated_at": time.time(),
            "message_count": 0
        }

    # Lazy load
    @property
    def messages(self) -> List[Message]:
        if self._messages is None:
            self._messages = self._load()
        return self._messages

    def _load(self) -> List[Message]:
        if not os.path.exists(self.path):
            return []

        with open(self.path, "r") as f:
            data = json.load(f)

        # load metadata if exists
        if "metadata" in data:
            self.metadata.update(data["metadata"])

        if "title" in data:
            self.title = data["title"]

        return [Message.from_dict(m) for m in data.get("messages", [])]

    def add(self, message: Message):
        self.messages.append(message)
        self.metadata["message_count"] = len(self.messages)
        self.metadata["updated_at"] = time.time()

    def save(self):
        dir_ = os.path.dirname(self.path)
        if dir_:
            os.makedirs(dir_, exist_ok=True)

        with open(self.path, "w") as f:
            json.dump({
                "id": self.id_,
                "title": self.title,
                "metadata": self.metadata,
                "messages": [m.to_dict() for m in self.messages]
            }, f, indent=2)

    def trim(self, max_messages: int = 50):
        if len(self.messages) > max_messages:
            self._messages = self.messages[-max_messages:]