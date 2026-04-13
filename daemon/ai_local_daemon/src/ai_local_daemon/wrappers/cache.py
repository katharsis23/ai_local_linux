import os
import json
from typing import Dict, List, Any
from datetime import datetime

from src.ai_local_daemon.models.chat import Chat   # adjust import if needed


class CacheManager:
    def __init__(self, cache_dir: str):
        self.cache_dir = os.path.expanduser(cache_dir)
        os.makedirs(self.cache_dir, exist_ok=True)

        self.chats: Dict[str, Chat] = {}
        self.index_path = os.path.join(self.cache_dir, "index.json")
        self._index: Dict[str, List[Dict]] = self._load_index()


    # ======================
    # Setup
    # ======================
    def setup(self):
        """Initialize and repair index if needed"""
        if not os.path.exists(self.index_path):
            self._rebuild_index()
            return

        try:
            self._index = self._load_index()
        except Exception:
            self._rebuild_index()

    # =====================
    # Index operations
    # =====================

    def _load_index(self) -> Dict[str, List[Dict]]:
        if not os.path.exists(self.index_path):
            return {"chats": []}
        with open(self.index_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_index(self):
        normalized = [
            self._normalize_entry(c)
            for c in self._index.get("chats", [])
        ]

        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump({"chats": normalized}, f, indent=2, ensure_ascii=False)

    def _rebuild_index(self):
        chats = []

        for file in os.listdir(self.cache_dir):
            if not file.endswith(".json") or file == "index.json":
                continue

            path = os.path.join(self.cache_dir, file)

            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                metadata = data.get("metadata", {})

                last_edited = metadata.get("last_edited")

                # normalize datetime
                if isinstance(last_edited, str):
                    last_edited_str = last_edited
                else:
                    last_edited_str = datetime.now().isoformat()

                chats.append({
                    "id": data.get("id"),
                    "title": data.get("title"),
                    "last_edited": last_edited_str,
                    "file_size": os.path.getsize(path),
                    "message_count": metadata.get("message_count", 0),
                })

            except Exception:
                continue

        self._index = {"chats": chats}
        self._save_index()
    # =====================
    # Chat operations
    # =====================

    def _chat_path(self, chat_id: str) -> str:
        # Support both "chat_xxx.json" and "xxx.json" formats
        if not chat_id.startswith("chat_"):
            return os.path.join(self.cache_dir, f"chat_{chat_id}.json")
        return os.path.join(self.cache_dir, f"{chat_id}.json")

    def load_chat(self, chat_id: str) -> Chat:
        if chat_id not in self.chats:
            chat = Chat(path=self._chat_path(chat_id))
            self.chats[chat_id] = chat
        return self.chats[chat_id]

    def create_chat(self, title: str = "New Chat") -> Chat:
        chat = Chat(title=title)
        self.chats[chat.id_] = chat

        # Save immediately to create file
        chat.save()

        size = os.path.getsize(chat.path)
        chat.metadata.file_size = size

        self._index["chats"].append({
            "id": chat.id_,
            "title": chat.title,
            "last_edited": chat.metadata.last_edited.isoformat(),
            "file_size": size,
            "message_count": chat.metadata.message_count,
        })

        self._save_index()
        return chat

    def save_chat(self, chat: Chat):
        chat.save()

        size = os.path.getsize(chat.path)

        # update runtime metadata
        chat.metadata.file_size = size

        entry = {
            "id": chat.id_,
            "title": chat.title,
            "last_edited": chat.metadata.last_edited.isoformat(),
            "file_size": size,
            "message_count": chat.metadata.message_count,
        }

        for i, c in enumerate(self._index["chats"]):
            if c.get("id") == chat.id_:
                self._index["chats"][i] = entry
                break
        else:
            self._index["chats"].append(entry)

        self._save_index()

    def list_chats(self) -> List[Dict]:
        return sorted(
            self._index["chats"],
            key=lambda x: x.get("last_edited") or "",
            reverse=True
        )

    def clear_all(self):
        for file in os.listdir(self.cache_dir):
            if file != "index.json":
                os.remove(os.path.join(self.cache_dir, file))
        self.chats.clear()
        self._index = {"chats": []}
        self._save_index()

    # =================
    # Helper
    # =================

    def _normalize_entry(self, entry: dict) -> dict:
        return {
            "id": entry.get("id", ""),
            "title": entry.get("title", ""),
            "last_edited": entry.get("last_edited") or datetime.now().isoformat(),
            "file_size": entry.get("file_size", 0),
            "message_count": entry.get("message_count", 0),
        }