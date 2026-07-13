from fastapi import APIRouter, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from logger import logger
from src.ai_local_daemon.internal.tool_calling import FileManager, DirectoryManager
from src.ai_local_daemon.dependency import get_approval_manager
from src.ai_local_daemon.internal.approval import ApprovalManager
from uuid import UUID
import asyncio


human_request_router = APIRouter(
    prefix="/request",
    tags=["human_request"],
)


manager: ApprovalManager = Depends(get_approval_manager)


@human_request_router.get("/ping")
async def ping_router():
    try:
        return JSONResponse(
            content={
                "status": "accepted"
            }
        )
    except HTTPException:
        logger.error(
            msg="Ping has failed",
            exc_info=True
        )


@human_request_router.get("/pending")
async def pending_requests(
    manager: ApprovalManager = Depends(get_approval_manager),
):
    print("1")

    await asyncio.sleep(0)

    print("2")

    queue = manager.notification_queue

    print("3", queue)

    coro = queue.get()

    print("4", coro)

    result = await asyncio.wait_for(coro, timeout=3)

    print("5")

    return result


@human_request_router.post("/approve/{request_id}")
async def approve_request(
    request_id: str,
    manager: ApprovalManager = Depends(get_approval_manager)
):
    # BUG: Does not return anything when TOOl EXECUTION FAILS
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
    state = manager.pending.get(UUID(request_id))

    if not state:
        raise HTTPException(404, "Request not found")

    state.request.approved = False

    # WAKE COROUTINE
    state.event.set()

    return {"status": "rejected"}
