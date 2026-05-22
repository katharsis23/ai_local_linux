from src.ai_local_daemon.models.approval import ApprovalRequest, ApprovalState
import os
from pathlib import Path
import asyncio
from typing import List, Dict
from uuid import UUID


class ApprovalManager:
    def __init__(self):
        self.pending: Dict[UUID, ApprovalState] = {}

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

            await state.event.wait()
            approved = bool(state.request.approved)

            del self.pending[state.request.id]

            return approved

        except Exception as error:
            raise error

    
