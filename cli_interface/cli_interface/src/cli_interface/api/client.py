import os
from typing import Optional

import httpx
from logger import logger


class ApiClient:
    def __init__(self, socket_path: Optional[str] = None):
        self.socket_path = (
            socket_path
            or f"/run/user/{os.getuid()}/ai_local_daemon/app.sock"
        )

        self._client = httpx.AsyncClient(
            transport=httpx.AsyncHTTPTransport(uds=self.socket_path),
            base_url="http://local",
            timeout=httpx.Timeout(60),
        )

    async def request(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> httpx.Response:
        try:
            response = await self._client.request(
                method=method,
                url=url,
                **kwargs,
            )

            response.raise_for_status()
            return response

        except httpx.HTTPStatusError:
            logger.error(
                "Server returned an error response.",
                exc_info=True,
            )
            raise

        except httpx.TransportError:
            logger.error(
                "Failed to connect to daemon.",
                exc_info=True,
            )
            raise

    async def healthcheck(self) -> bool:
        try:
            response = await self.request(
                "GET",
                "/healthcheck/",
            )
            return response.status_code == 200

        except httpx.HTTPError:
            return False

    async def close(self):
        await self._client.aclose()