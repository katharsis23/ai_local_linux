from src.cli_interface.api.client import ApiClient
from src.cli_interface.models.chat import Chat, Messages


class ChatClient:
    def __init__(self, api: ApiClient):
        self.api = api

    async def get_chats(self) -> Chat:
        response = await self.api.request(
            "GET",
            "/chat/list",
        )

        body = response.json()

        return Chat.from_dict(
            body.get("chats", [])
        )

    async def get_chat(self, chat_id: str):
        response = await self.api.request(
            "GET",
            f"/chat/{chat_id}",
        )

        body = response.json()

        metadata = body.get("metadata", {})
        messages = Messages.from_dict(
            body.get("messages", [])
        )

        return metadata, messages

    async def create_chat(self, title: str | None = None) -> str:
        response = await self.api.request(
            "POST",
            "/chat/create",
            json={
                "title": title,
            },
        )

        return response.json()["id"]