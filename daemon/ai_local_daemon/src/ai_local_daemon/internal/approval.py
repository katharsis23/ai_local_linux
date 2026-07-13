from src.ai_local_daemon.models.approval import ApprovalRequest, ApprovalState
import os
from pathlib import Path
import asyncio
from typing import List, Dict
from uuid import UUID
# import asyncio


class ApprovalManager:
    def __init__(self):
        self.pending: Dict[UUID, ApprovalState] = {}
        self.notification_queue = asyncio.Queue()

    async def make_request(
        self,
        type_: str,
        path: str | None = None,
        command: str | None = None,
    ):
        try:
            request = ApprovalRequest(
                type_=type_,
                path=path,
                command=command,
            )
            state = ApprovalState(request=request)
            self.pending[state.request.id] = state
            await self.notification_queue.put(state.request)

            await asyncio.wait_for(
                state.event.wait(),
                timeout=650
            )
            # add enum in ApprovalState for more variables
            approved = bool(state.request.approved)

            return approved

        except Exception as error:
            raise error

        finally:
            self.pending.pop(state.request.id, None)
