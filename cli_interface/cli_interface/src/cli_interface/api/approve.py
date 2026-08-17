from src.cli_interface.api.client import ApiClient
from src.cli_interface.models.approval import Approval
import asyncio
from logger import logger
import httpx as http


class ApproveAPI:
    def __init__(self, api: ApiClient):
        self.api = api

    async def reject(self, request_id: str):
        response = await self.api.request("POST", f"/request/reject/{request_id}")
        return response.json()

    async def pending_requests(self) -> Approval | None:
        try:
            response = await self.api.request("GET", "/request/pending")
            return Approval.from_dict(response.json())
        except http.ReadTimeout:
            # Long-polling timeouts are expected when there's no pending request
            return None
        except http.HTTPStatusError as e:
            if e.response.status_code == 408:
                return None
            raise
        except http.HTTPError:
            logger.error(
                "Failed to get pending approves",
                exc_info=True
            )
            return None

    async def approve(self, request_id: str):
        response = await self.api.request("POST", f"/request/approve/{request_id}")
        return response.json()
