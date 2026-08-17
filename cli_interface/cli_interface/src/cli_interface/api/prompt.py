from src.cli_interface.api.client import ApiClient


class PromptClient:
    def __init__(self, api: ApiClient):
        self.api = api

    async def send_prompt(
        self,
        prompt: str,
        chat_id: str | None = None,
    ) -> str:
        response = await self.api.request(
            "POST",
            "/chat/prompt/",
            data={
                "prompt": prompt,
            },
            params={
                "chat_id": chat_id,
            } if chat_id else None,
        )

        return response.json()["response"]
