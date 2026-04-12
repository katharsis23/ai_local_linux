# cache_manager.py
import os
import json
from typing import Dict, List
from src.ai_local_daemon.models.chat import Chat


class CacheManager:
    def __init__(self, cache_dir: str):
        self.cache_dir = os.path.expanduser(cache_dir)
        os.makedirs(self.cache_dir, exist_ok=True)

        self.chats: Dict[str, Chat] = {}
        self.index_path = os.path.join(self.cache_dir, "index.json")

        self._index = self._load_index()

    # -------------------------
    # Index handling
    # -------------------------

    def _load_index(self) -> dict:
        if not os.path.exists(self.index_path):
            return {"chats": []}

        with open(self.index_path, "r") as f:
            return json.load(f)

    def _save_index(self):
        with open(self.index_path, "w") as f:
            json.dump(self._index, f, indent=2)

    # -------------------------
    # Core operations
    # -------------------------

    def _chat_path(self, chat_id: str) -> str:
        return os.path.join(self.cache_dir, f"{chat_id}.json")

    def load_chat(self, chat_id: str) -> Chat:
        if chat_id not in self.chats:
            chat = Chat(path=self._chat_path(chat_id))
            self.chats[chat_id] = chat
        return self.chats[chat_id]

    def create_chat(self, title: str = "New Chat") -> Chat:
        chat = Chat(
            path=os.path.join(self.cache_dir, f"chat_{os.urandom(4).hex()}.json"),
            title=title
        )

        self.chats[chat.id_] = chat

        self._index["chats"].append({
            "id": chat.id_,
            "title": chat.title,
            "updated_at": chat.metadata["updated_at"]
        })

        self._save_index()
        return chat

    def save_chat(self, chat: Chat):
        chat.save()

        # update index
        for c in self._index["chats"]:
            if c["id"] == chat.id_:
                c["title"] = chat.title
                c["updated_at"] = chat.metadata["updated_at"]
                break

        self._save_index()

    # -------------------------
    # Listing / selection
    # -------------------------

    def list_chats(self) -> List[dict]:
        return sorted(
            self._index["chats"],
            key=lambda x: x["updated_at"],
            reverse=True
        )

    def get_titles(self) -> List[str]:
        return [c["title"] for c in self._index["chats"]]

    # -------------------------
    # Maintenance
    # -------------------------

    def reload(self):
        self.chats.clear()
        self._index = self._load_index()

    def clear_all(self):
        for file in os.listdir(self.cache_dir):
            os.remove(os.path.join(self.cache_dir, file))

        self.chats.clear()
        self._index = {"chats": []}
        self._save_index()