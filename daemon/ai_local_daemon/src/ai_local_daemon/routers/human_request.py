from fastapi import APIRouter, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from logger import logger
from src.ai_local_daemon.internal.tool_calling import FileManager, DirectoryManager
from src.ai_local_daemon.dependency import get_approval_manager
from src.ai_local_daemon.internal.approval import ApprovalManager
from uuid import UUID


human_request_router = APIRouter(
    prefix="/request",
    tags=["human_request"],
)


manager: ApprovalManager = Depends(get_approval_manager)


@human_request_router.get("/pending")
async def pending_requests(manager: ApprovalManager = Depends(get_approval_manager)):

    return [
            state.request
        for state in manager.pending.values()
    ]


@human_request_router.post("/approve/{request_id}")
async def approve_request(
    request_id: str,
    manager: ApprovalManager = Depends(get_approval_manager)
):

    state = manager.pending.get(UUID(request_id))

    if not state:
        raise HTTPException(404, "Request not found")

    state.request.approved = True

    # WAKE COROUTINE
    state.event.set()

    return {"status": "approved"}


@human_request_router.post("/reject/{request_id}")
async def reject_request(
    request_id: str,
    manager: ApprovalManager = Depends(get_approval_manager)
):

    state = manager.pending.get(request_id)

    if not state:
        raise HTTPException(404, "Request not found")

    state.request.approved = False

    # WAKE COROUTINE
    state.event.set()

    return {"status": "rejected"}
